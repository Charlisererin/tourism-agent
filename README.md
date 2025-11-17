# 24年计设国三作品

基于多模态AI+Django+MySQL的旅游景点推荐系统

## 环境要求

- Python 3.7或Python 3.8
- MySQL 5.7/8.0
- MongoDB
- 相关Python依赖包

## 安装步骤

### 1. 安装依赖包

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

修改`ai_tourism_recommend/settings.py`文件中的数据库配置信息：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tourism_recommend',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 3.导入数据

- tourism_recommend.sql 导入到MySQL数据库
- qianwen_logs.sql 导入MongoDB数据库
- qianwen_memory.sql 导入MongoDB数据库

### 4.多模态AI配置

`ai_tourism_recommend\app\.env` 目录修改自己的Mongo配置和阿里百炼平台key

### 5. 访问系统

在终端执行 `python manage.py runserver` 进入前端页面
（通常是 http://127.0.0.1:8000/ ）即可访问系统。

```markdown
管理员
地址：http://127.0.0.1:8000/admin
账号：admin
密码：admin

普通用户
地址：http://127.0.0.1:8000/
账号：test
密码：123456
也可以自己注册
```

## 使用截图

![image](img/1.png)
![image](img/2.png)
![image](img/3.png)
![image](img/4.png)
![image](img/5.png)
![image](img/6.png)
![image](img/7.png)
![image](img/8.png)
![image](img/9.png)
![image](img/10.png)
![image](img/11.png)
![image](img/12.png)
![image](img/13.png)
![image](img/14.png)
![image](img/15.png)
![image](img/16.png)
![image](img/17.png)
![image](img/18.png)
![image](img/19.png)
![image](img/20.png)
![image](img/21.png)
![image](img/22.png)
![image](img/23.png)
![image](img/24.png)
![image](img/25.png)

