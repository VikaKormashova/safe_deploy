import re
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]{4,20}$')
    email: EmailStr
    password: str
    confirm_password: str
    age: int = Field(..., ge=18, le=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Проверка сложности пароля"""
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Пароль должен содержать минимум 1 заглавную букву')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Пароль должен содержать минимум 1 цифру')
        
        if not re.search(r'[!@#$%^&*]', v):
            raise ValueError('Пароль должен содержать минимум 1 спецсимвол (!@#$%^&*)')
        
        return v
    
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserCreate':
        """Проверка совпадения паролей"""
        if self.password != self.confirm_password:
            raise ValueError('Пароли не совпадают')
        return self