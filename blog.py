from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#Kullanıcı giriş decorator:
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args ,**kwargs)
        
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız...","danger")
            return redirect(url_for("login"))
    
    return decorated_function





#Kullanıcı kayıt formu:
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25,message="4 ile 25 karakter uzunluğunda olmalı")])
    username = StringField("Kullanıcı adı",validators=[validators.Length(min = 4,max = 25,message="4 ile 25 karakter uzunluğunda olmalı")])
    email = StringField("Email Adresi",validators=[validators.Email(message="Lütfen Geçerli Bir E-mail giriniz.")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message= "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolanız uyuşmuyor...")

    ])
    confirm = PasswordField("Parola Doğrula")
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")




app = Flask(__name__)
app.secret_key = "jpblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "jpblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.xhtml")

@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) Values(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarı ile kayıt oldunuz...","success")
        
        return redirect(url_for("login"))

    else:
        return render_template("register.xhtml",form = form)


@app.route("/about")
def about():
    return render_template("about.xhtml")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author= %s"

    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.xhtml",articles = articles)
    
    else:
        return render_template("dashboard.xhtml")
    


#Login işlemi
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız...","success")
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index")) 
            else:
                flash("Parolanızı Yanlış Girdiniz...","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    
    return render_template("login.xhtml",form = form)
#logout:
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yaptınız...","success")
    return redirect(url_for("index"))

#Makale detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id = %s"
    
    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()

        return render_template("article.xhtml", article = article)

    else:
        return render_template("article.xhtml")

#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    
    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        
        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok.","danger")
        
        return redirect(url_for("index"))

#Makale güncelleme
@app.route("/edit/<string:id>",methods = ["POST","GET"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where id = %s and author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok...","danger")
            return redirect(url_for("index"))
        
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.xhtml",form = form)
    #post request kısmı
    else:
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newcontent = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newcontent,id))
        mysql.connection.commit()
        flash("Makaleniz Güncellendi..","success")
        return redirect(url_for("dashboard"))






#Makale ekleme
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert Into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        
        mysql.connection.commit()

        cursor.close()

        flash("Makale Başarı ile Eklendi..","success")

        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.xhtml",form = form)

#Makale sayfası:
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.xhtml",articles = articles)
    else:
        return render_template("articles.xhtml")






#Makale Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=0,max=100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=15,max=1100)])

#arama url
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan kelimeye uygun makale bulunmadı..","danger")
            
            return redirect(url_for("articles"))
            
        else:
            articles = cursor.fetchall()

            return render_template("articles.xhtml",articles = articles)



if __name__ == "__main__":
    app.run(debug=True)
