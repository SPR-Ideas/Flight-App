from fastapi import APIRouter , Request
from datetime import timedelta
from fastapi.templating import Jinja2Templates
from starlette.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from fastapi_login import LoginManager
from passlib.context import CryptContext
from database.database import SessionLocal
from database.models import user
from fastapi_login.exceptions import InvalidCredentialsException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse ,JSONResponse ,RedirectResponse


user_app = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET = "f98e623de44d967238ee8dedc886860b65683b9ba0ce6efd"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
manager = LoginManager(SECRET, '/token' ,use_cookie=True ,use_header=True)


def get_hash_pwd(passwd):
    """Returns hased pwd."""
    return pwd_context.hash(passwd)


class UserPd(BaseModel):
    """ It is a pydantic model of user instance"""
    username : str
    name : str
    password : str
    location : str


@user_app.post("/login_user")
async def login_user(response: Response, data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password

    user_instance = query_user(username)

    if not user_instance:
        raise InvalidCredentialsException

    matches_passwd = pwd_context.verify(password,user_instance.password)

    if not matches_passwd:
        # If password matches raises Invalid credentials.
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data={'sub': username},
        expires = timedelta(hours = 12)
    )

    # It set the Token in cookies for the user.
    manager.set_cookie(response, access_token)
    return {'token': access_token}


@manager.user_loader
def query_user(username: str):
    """
    Get a user from the db
    :param user_id: E-Mail of the user
    :return: None or the user object
    """
    session = SessionLocal()
    user_object = session.query(user).filter(user.username == username).first()

    if user_object:
        return user_object
    return None


def create_user(user_instance):
    """It creat an user in db."""
    session = SessionLocal()
    hash_pwd = get_hash_pwd(user_instance.password)
    user_object = user(
        username = user_instance.username,
        name = user_instance.name ,
        password = hash_pwd,
        location = user_instance.location
    )
    session.add(user_object)
    session.commit()
    session.close()


@user_app.post("/create-user")
def create_user_by_route(user_instance : UserPd ):
    """It just creats an user and gives us status."""
    session = SessionLocal()
    username = user_instance.username
    exisiting_user = session.query(user).filter(user.username == username).first()
    if exisiting_user :
        return JSONResponse(status_code=401, content={
                "error":"1",            # Should be changed by exception.
                "msg":"username exist."
            } )

    create_user(user_instance)
    return JSONResponse(status_code=200,content= {
        "error" : "0",
        "msg" : "Success"
    }   )



@user_app.get("/login")
def login(request : Request):
        return templates.TemplateResponse(
        "login.html",{"request":request}
    )
    # return "HI"


@user_app.get("/",response_class=HTMLResponse)
def home(request:Request, user_instance = Depends(manager)):
    """
        Returns HomePage if user is autheticated,
        if not it redirect to login page.
    """


    return templates.TemplateResponse(
        "home.html",{"request":request}
    )



