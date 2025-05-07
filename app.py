from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI()

# Kullanıcı modelleri
class User(BaseModel):
    username: str
    role: str

class UserInDB(User):
    hashed_password: str

# Sahte kullanıcı verisi
fake_users_db = {
    "mehmet": {
        "username": "mehmet",
        "role": "user",
        "hashed_password": "fakehashed123"
    },
    "admin": {
        "username": "admin",
        "role": "admin",
        "hashed_password": "fakehashedadmin"
    }
}

# JWT ayarları
SECRET_KEY = "secret123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Hash fonksiyonu (gerçek değil, demo)
def fake_hash_password(password: str):
    return "fakehashed" + password

# Kullanıcı verisi alma
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

# Giriş doğrulama
def authenticate_user(username: str, password: str):
    user = get_user(fake_users_db, username)
    if not user or user.hashed_password != fake_hash_password(password):
        return None
    return user

# Token oluşturma
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Token doğrulama
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Giriş doğrulanamadı",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username)
    if user is None:
        raise credentials_exception
    return User(username=user.username, role=user.role)

# Token endpointi
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Kullanıcı adı veya şifre yanlış")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def root():
    return {"message": "To-Do App çalışıyor!"}

@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return current_user

# MODELLER

class ToDoListCreate(BaseModel):
    name: str

class ToDoList(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    user: str
    completion_percentage: float

class ToDoItemCreate(BaseModel):
    list_id: int
    description: str

class ToDoItem(BaseModel):
    id: int
    list_id: int
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

# VERİ TUTUCULAR
todo_lists = []
todo_items = []
list_id_counter = 1
item_id_counter = 1

# TAMAMLANMA ORANINI GÜNCELLE
def update_completion_percentage(list_id: int):
    items = [i for i in todo_items if i["list_id"] == list_id and i["deleted_at"] is None]
    completed = [i for i in items if i["completed"]]
    percentage = (len(completed) / len(items)) * 100 if items else 0.0
    for lst in todo_lists:
        if lst["id"] == list_id:
            lst["completion_percentage"] = round(percentage, 2)

# LİSTE OLUŞTUR
@app.post("/lists", response_model=ToDoList)
def create_list(list_data: ToDoListCreate, current_user: User = Depends(get_current_user)):
    global list_id_counter
    new_list = {
        "id": list_id_counter,
        "name": list_data.name,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted_at": None,
        "user": current_user.username,
        "completion_percentage": 0.0
    }
    todo_lists.append(new_list)
    list_id_counter += 1
    return new_list

# TÜM LİSTELERİ GÖR
@app.get("/lists", response_model=List[ToDoList])
def get_lists(current_user: User = Depends(get_current_user)):
    return [lst for lst in todo_lists if lst["user"] == current_user.username and lst["deleted_at"] is None]

# ADIM EKLE
@app.post("/items", response_model=ToDoItem)
def create_item(item_data: ToDoItemCreate, current_user: User = Depends(get_current_user)):
    global item_id_counter
    # Liste kontrol
    related_list = next((lst for lst in todo_lists if lst["id"] == item_data.list_id and lst["user"] == current_user.username and lst["deleted_at"] is None), None)
    if not related_list:
        raise HTTPException(status_code=404, detail="Liste bulunamadı")
    # Yeni item
    new_item = {
        "id": item_id_counter,
        "list_id": item_data.list_id,
        "description": item_data.description,
        "completed": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted_at": None
    }
    todo_items.append(new_item)
    item_id_counter += 1
    update_completion_percentage(item_data.list_id)
    return new_item

# ADIMLARI GÖR
@app.get("/items", response_model=List[ToDoItem])
def get_items(current_user: User = Depends(get_current_user)):
    return [
        item for item in todo_items
        if any(lst for lst in todo_lists if lst["id"] == item["list_id"] and lst["user"] == current_user.username)
        and item["deleted_at"] is None
    ]
