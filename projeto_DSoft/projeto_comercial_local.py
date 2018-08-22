from flask import Flask, render_template,redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from functools import wraps
from flask_uploads import UploadSet,configure_uploads,ALL
from firebase import firebase
import pyrebase
import json

with open('teste.txt','r') as file:
    data = json.loads(file.read())
#Configura firebase por pyrebase
firebase2 = firebase.FirebaseApplication('https://projeto-desoft-7e877.firebaseio.com/')
config = {
  "apiKey": "apiKey",
  "authDomain": "projeto-desoft.firebaseapp.com",
  "databaseURL": "projeto-desoft-7e877.firebaseio.com/",
  "storageBucket": "projeto-desoft-7e877.appspot.com"
}
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
database = firebase.database()

#Flask app
app = Flask(__name__)
#Salvar arquivos internamente usando Upload set#
arquivos = UploadSet('inputarquivo', ALL)
app.config['UPLOADED_INPUTARQUIVO_DEST'] = 'static/arquivos'
configure_uploads(app,arquivos)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gdhelp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Acesso Negado!")
            return redirect(url_for('login'))
    return wrap

# Index
@app.route('/')
def index():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register',methods=["GET","POST"])
def register():
    status_cadastro = 0
    mensagem_erro=''
    if request.method=="POST":
        mensagem_erro= ''
        status_cadastro = 0
        name = request.form['Name']
        username=request.form['userName']
        email = str(request.form['eMail'])
        password=request.form['passWord']
        confpassword=request.form['confPassword']
        cur = mysql.connection.cursor()
        resultado = cur.execute("SELECT * FROM users WHERE username=%s",[username])
        if resultado == 0:
            if len(name) == 0:
                mensagem_erro = "Nome nao poder ser vazio!"
                return render_template('register.html',mensagem_erro=mensagem_erro)
            elif len(username)== 0:
                mensagem_erro="Usuario nao pode ser vazio!"
                return render_template('register.html',mensagem_erro=mensagem_erro)
            elif len(email)== 0:
                mensagem_erro="Insira um e-mail valido!"
                return render_template('register.html',mensagem_erro=mensagem_erro)
            elif len(password) == 0:
                mensagem_erro="Senha nao poder ser vazio!"
                return render_template('register.html',mensagem_erro=mensagem_erro)
            elif confpassword != password:
                mensagem_erro="Senhas nao condizem!"
                return render_template('register.html',mensagem_erro=mensagem_erro)
            else:
                mensagem_sucesso="Cadastro realizado com sucesso!"
                status_cadastro = 1
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users(name,username,email,password) VALUES (%s,%s,%s,%s)",(name,username,email,password))
            cur.connection.commit()
            cur.close()
            data = {"Nome":name,"Username":username,"Email":email,"Password":password}
            firebase2.put('/Users',"{}".format(username),data)
            return redirect(url_for('login'))
        elif resultado > 0:
            error = "Username nao Disponivel!"
            return render_template('register.html',mensagem_erro =error)

    return render_template('register.html')
@app.route('/login',methods=["POST","GET"])
def login():
    sucesso=''
    error=''
    if request.method == "POST":
        username = request.form['userName']
        password_input=request.form['passWord']
        cur = mysql.connection.cursor()
                # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            sucesso = ""                    # Get stored hash
            data = cur.fetchone()
            password = data['password']
            # Compare Passwords
            if password == password_input:
                        # Passed
                session['logged_in'] = True
                session['username'] = username
                status = "Você esta loggado!"
                return redirect(url_for('menu'))
                cur.close()
            else:
                error = 'Login Invalido!'
                return render_template('login.html', error=error)
                    # Close connection
                cur.close()
        else:
            error = 'Username não existente!'
            return render_template('login.html', error=error)
            cur.close()

    return render_template('login.html')

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    mensagem = "Voce nao esta mais logado!"
    return redirect(url_for('login'))
@app.route('/upload',methods=["GET","POST"])
@is_logged_in
def upload():
    if request.method == "POST" and 'inputarquivo' in request.files:
        arquivo = request.files['inputarquivo']
        titulo = request.form['inputtitulo']
        autor = session['username']
        local = request.form['local']
        tipo = request.form['tipo']
        if local == "Interno":
            cur = mysql.connection.cursor()
            titulojunto = titulo.replace(" ","_")
            url = "{}.{}".format(titulojunto,tipo)
            cur.execute("INSERT INTO arquivos(titulo,autor,local,tipo,url) VALUES(%s,%s,%s,%s,%s)",(titulo,autor,local,tipo,url))
            cur.connection.commit()
            cur.close()
            filename = arquivos.save(request.files['inputarquivo'],name=url)
            status = "Arquivo Salvo em disco interno!"
            return render_template('uploads.html',status=status)
        elif local == "Firebase":
            storage.child("{}.{}".format(titulo,tipo)).put(arquivo)
            url = storage.child("{}.{}".format(titulo,tipo)).get_url(None)
            print(url)
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO arquivos(titulo,autor,local,tipo,url) VALUES(%s,%s,%s,%s,%s)",(titulo,autor,local,tipo,url))
            cur.connection.commit()
            cur.close()
            status = "Arquivo Salvo no Firebase com Sucesso!"
            return render_template('uploads.html',status=status)

    return render_template('uploads.html')

@app.route('/menu',methods=["GET","POST"])
@is_logged_in
def menu():
    username = session['username']
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM arquivos")
    arquivos = cur.fetchall()
    cur.execute("SELECT * FROM users WHERE username=%s",[username])
    usuario = cur.fetchone()
    if result > 0:
        return render_template('menu2.html', arquivos=arquivos,usuario=usuario)
    else:
        msg = 'Nenhum arquivo foi encontrado!'
        return render_template('menu2.html', msg=msg)
    # Close connection
    cur.close()
    return render_template('menu2.html')

@app.route('/preview/<int:id>/')
@is_logged_in
def article(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM arquivos WHERE id = %s", [id])
    arquivo = cur.fetchone()
    data = cur.execute("SELECT file FROM arquivos WHERE id = %s", [id])
    filedata = cur.fetchone()
    tipo = arquivo['tipo']
    local = arquivo['local']
    print(filedata)
    return render_template('preview.html',arquivo=arquivo,tipo=tipo,local=local)

@app.route('/minha-conta')
@is_logged_in
def Minhaconta():
    username = session['username']
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
    usuario = cur.fetchone()
    result2 = cur.execute("SELECT * FROM arquivos WHERE autor=%s",[username])
    arquivos = cur.fetchall()
    print(arquivos)
    cur.close()
    return render_template('minhaconta.html',usuario=usuario,arquivo=arquivos)

@app.route('/changename',methods=["GET","POST"])
@is_logged_in
def Changename():
    if request.method == "POST":
        username = session['username']
        novo_nome = request.form['newName']
        password = request.form['passWord']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        if password == usuario['password']:
            cur.execute("UPDATE users set name=%s WHERE username=%s",[novo_nome,username])
            cur.connection.commit()
            cur.close()
            sucesso = "Nome alterado com sucesso!"
            data = {"Nome":novo_nome,"Username":usuario['username'],"Email":usuario['email'],"Password":password}
            firebase2.put('/Users',"{}".format(username),data)
            return render_template('changename.html',sucesso=sucesso)
        elif len(novo_nome) == 0:
            erro = "Nome não pode ser vazio!"
            return render_template('changename.html',error = erro)
        elif password != usuario['password']:
            erro="Login Invalido!"
            return render_template('changename.html',error = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('changename.html',error = erro)
    return render_template('changename.html')

@app.route('/change-username',methods=["GET","POST"])
@is_logged_in
def Changeuser():
    if request.method == "POST":
        username = session['username']
        novo_username = request.form['newUser']
        password = request.form['passWord']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        if password == usuario['password']:
            firebase2.delete('/Users/{}'.format(username),None)
            cur.execute("UPDATE users set username=%s WHERE username=%s",[novo_username,username])
            cur.execute("UPDATE arquivos SET autor=%s WHERE autor=%s",[novo_username,username])
            cur.connection.commit()
            cur.close()
            sucesso = "Username alterado com sucesso!"
            session['username'] = novo_username
            data = {"Nome":usuario['name'],"Username":novo_username,"Email":usuario['email'],"Password":password}
            firebase2.put('/Users',"{}".format(novo_username),data)
            return render_template('changeusername.html',sucesso=sucesso)
        elif len(novo_username) == 0:
            erro = "Username não pode ser vazio!"
            return render_template('changeusername.html',error = erro)
        elif password != usuario['password']:
            erro="Login Invalido!"
            return render_template('changeusername.html',error = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('changeusername.html',error = erro)
    return render_template('changeusername.html')

@app.route('/change-email',methods=["GET","POST"])
@is_logged_in
def Changeemail():
    if request.method == "POST":
        username = session['username']
        novo_email = request.form['newEmail']
        password = request.form['passWord']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        if password == usuario['password']:
            cur.execute("UPDATE users set email=%s WHERE username=%s",[novo_email,username])
            cur.connection.commit()
            cur.close()
            sucesso = "Email alterado com sucesso!"
            data = {"Nome":usuario['name'],"Username":username,"Email":novo_email,"Password":password}
            firebase2.put('/Users',"{}".format(username),data)
            return render_template('change-email.html',sucesso=sucesso)
        elif len(novo_email) == 0:
            erro = "Email não pode ser vazio!"
            return render_template('change-email.html',error = erro)
        elif password != usuario['password']:
            erro="Login Invalido!"
            return render_template('change-email.html',error = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('change-email.html',error = erro)
    return render_template('change-email.html')

@app.route('/changepassword',methods=["GET","POST"])
@is_logged_in
def Changepassword():
    if request.method == "POST":
        username = session['username']
        novo_password = request.form['newPassword']
        password = request.form['passWord']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        if password == usuario['password']:
            cur.execute("UPDATE users set password=%s WHERE username=%s",[novo_password,username])
            cur.connection.commit()
            cur.close()
            sucesso = "Senha alterada com sucesso!"
            data = {"Nome":usuario['name'],"Username":username,"Email":usuario['email'],"Password":novo_password}
            firebase2.put('/Users',"{}".format(username),data)
            return render_template('change-password.html',sucesso=sucesso)
        elif len(novo_password) == 0:
            erro = "Nova senha não pode ser vazio!"
            return render_template('change-password.html',error = erro)
        elif password != usuario['password']:
            erro="Login Invalido!"
            return render_template('change-password.html',error = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('change-password.html',error = erro)
    return render_template('change-password.html')
@app.route('/delete/<titulo>')
@is_logged_in
def delete(titulo):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM arquivos WHERE titulo=%s",[titulo])
    cur.connection.commit()
    cur.close()
    return redirect(url_for('menu'))






if __name__ == '__main__':
    app.secret_key='gdhelp12'
    app.run(debug=True)
