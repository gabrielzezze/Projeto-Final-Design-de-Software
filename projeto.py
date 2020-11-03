from flask import Flask, render_template,redirect, url_for, session, request
import mysql.connector
from functools import wraps
from flask_uploads import UploadSet,configure_uploads,ALL
from firebase import firebase
import pyrebase
import json
import string
from random import *
import smtplib
from passlib.hash import sha256_crypt
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

min_char = 8
max_char = 14
allchar = string.ascii_letters + string.punctuation + string.digits

with open('teste.txt','r') as file:
    data = json.loads(file.read())
#Configura firebase por pyrebase
firebase2 = firebase.FirebaseApplication('https://pybox-62c8f.firebaseio.com/')
config = {
  "apiKey": "apiKey",
  "authDomain": "pybox-62c8f.firebaseapp.com",
  "databaseURL": "https://pybox-62c8f.firebaseio.com/",
  "storageBucket": "pybox-62c8f.appspot.com"
}
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
database = firebase.database()

#Flask app
app = Flask(__name__)
#Salvar arquivos internamente usando Upload set#
arquivos = UploadSet('inputarquivo', ALL)
app.config['UPLOADED_INPUTARQUIVO_DEST'] = '/home/zezzebr/Teste_Projeto/static/arquivos'
configure_uploads(app,arquivos)
#Email sending#

#app.config.update(DEBUG=True,MAIL_SERVER='smtp.gmail.com',MAIL_PORT=465,MAIL_USE_SSL=True,MAIL_USERNAME='pybox.manager@gmail.com',MAIL_PASSWORD='pybox321')
#mail = Mail(app)

# Config MySQL
conn = mysql.connector.connect(user='pybox',password='Pybox12345',host='pybox.mysql.pythonanywhere-services.com',database='pybox$pybox')
app.secret_key='pybox12354'

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:

            return redirect(url_for('login'))
    return wrap

def is_logged_out(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' not in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('menu'))
    return wrap


# Index
@app.route('/')
def index():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register',methods=["GET","POST"])
@is_logged_out
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
        cur = conn.cursor(buffered=True)
        if username == '':
            mensagem_erro = "Username não pode ser vazio!"
            cur.close()
            return render_template('register.html',mensagem_erro=mensagem_erro)
        else:
            cur = conn.cursor(buffered=True)
            cur.execute("SELECT * FROM users WHERE username=%s",[username])
            resultado = cur.fetchone()
            print(resultado)
            if resultado == None:
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
                cur = conn.cursor()
                password_crypt = sha256_crypt.encrypt(str(password))
                cur.execute("INSERT INTO users(name,username,email,password) VALUES (%s,%s,%s,%s)",(name,username,email,password_crypt))
                conn.commit()
                cur.close()
                data = {"Nome":name,"Username":username,"Email":email,"Password":password_crypt}
                firebase2.put('/Users',"{}".format(username),data)
                return redirect(url_for('login'))
            elif resultado != None:
                error = "Username nao Disponivel!"
                return render_template('register.html',mensagem_erro =error)

    return render_template('register.html')
@app.route('/login',methods=["POST","GET"])
@is_logged_out
def login():
    sucesso=''
    error=''
    if request.method == "POST":
        username = request.form['userName']
        password_input=request.form['passWord']
        password_candidate = sha256_crypt.encrypt(str(password_input))
        cur = conn.cursor(buffered=True)
                # Get user by username
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        data = cur.fetchone()
        if data != None:
            sucesso = ""
            print(data)
            password = data[4]
            print(password)
            # Compare Passwords
            if sha256_crypt.verify(password_input, password):
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

@app.route('/recuperar-senha',methods=["GET","POST"])
@is_logged_out
def Recoverpassword():
    if request.method == "POST":
        email = request.form['emailrecovery']
        cur = conn.cursor(buffered=True)
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        usuario = cur.fetchone()
        cur.close()
        if usuario != None:
            cur = conn.cursor()
            codigo_acesso = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
            codigo_acesso_final = sha256_crypt.encrypt(codigo_acesso)
            cur.execute("UPDATE users SET password=%s WHERE email = %s", [codigo_acesso_final,email])
            conn.commit()
            cur.close()
            msg = MIMEMultipart()
            password = 'pybox321'
            msg['From'] = 'pybox.manager@gmail.com'
            msg['To'] = '{}'.format(email)
            msg['Subject'] = "Recuperação de senha PyBox"
            msg.attach(MIMEText('Conforme solicitado segue seu codigo de acesso provisório ao PyBox por favor acessar sua conta utilizando este codigo e alterar sua senha para uma senha deseja. Codigo de acesso= {} -Team PyBox'.format(codigo_acesso)))
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(msg['From'], password)
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
            sucesso = "Verifique seu email para recuperar sua senha!"
            return render_template('passwordrecovery.html',sucesso=sucesso)
        else:
            erro = "E-mail Invalido!"
            return render_template('passwordrecovery.html',error=erro)
    return render_template('passwordrecovery.html')

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
        print(arquivo)
        print(arquivo.filename)
        nome_arquivo = arquivo.filename
        tipo = nome_arquivo[nome_arquivo.rindex('.')+1:]
        print(tipo)
        if local == "Firebase-privado":
            storage.child("{}.{}".format(titulo,tipo)).put(arquivo)
            url = storage.child("{}.{}".format(titulo,tipo)).get_url(None)
            print(url)
            cur = conn.cursor()
            cur.execute("INSERT INTO arquivos(titulo,autor,local,tipo,url,publico) VALUES(%s,%s,%s,%s,%s,%s)",(titulo,autor,local,tipo,url,False))
            conn.commit()
            cur.close()
            status = "Arquivo Salvo no Firebase com Sucesso!"
            return render_template('uploads.html',status=status)
        elif local == "Firebase":
            storage.child("{}.{}".format(titulo,tipo)).put(arquivo)
            url = storage.child("{}.{}".format(titulo,tipo)).get_url(None)
            print(url)
            cur = conn.cursor()
            cur.execute("INSERT INTO arquivos(titulo,autor,local,tipo,url,publico) VALUES(%s,%s,%s,%s,%s,%s)",(titulo,autor,local,tipo,url,True))
            conn.commit()
            cur.close()
            status = "Arquivo Salvo no Firebase com Sucesso!"
            return render_template('uploads.html',status=status)

    return render_template('uploads.html')

@app.route('/menu',methods=["GET","POST"])
@is_logged_in
def menu():
    username = session['username']
    cur = conn.cursor()
    result = cur.execute("SELECT * FROM arquivos WHERE publico IS TRUE")
    arquivos = cur.fetchall()
    if arquivos != None:
        cur.execute("SELECT * FROM users WHERE username=%s",[username])
        usuario = cur.fetchone()
        print(usuario)
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
    cur = conn.cursor()
    cur.execute("SELECT * FROM arquivos WHERE id = %s", [id])
    arquivo = cur.fetchone()
    return render_template('preview.html',arquivo=arquivo)

@app.route('/minha-conta')
@is_logged_in
def Minhaconta():
    username = session['username']
    cur = conn.cursor()
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
        password_candidate = sha256_crypt.encrypt(password)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        if sha256_crypt.verify(password, usuario[4]):
            cur.execute("UPDATE users set name=%s WHERE username=%s",[novo_nome,username])
            conn.commit()
            cur.close()
            sucesso = "Nome alterado com sucesso!"
            data = {"Nome":novo_nome,"Username":username,"Email":usuario[3],"Password":usuario[4]}
            firebase2.put('/Users',"{}".format(username),data)
            return render_template('changename.html',mensagem_sucesso=sucesso)
        elif len(novo_nome) == 0:
            erro = "Nome não pode ser vazio!"
            return render_template('changename.html',mensagem_erro = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('changename.html',mensagem_erro = erro)
        else:
            erro="Login Invalido!"
            return render_template('changename.html',mensagem_erro = erro)
    return render_template('changename.html')

@app.route('/change-username',methods=["GET","POST"])
@is_logged_in
def Changeuser():
    if request.method == "POST":
        username = session['username']
        novo_username = request.form['newUser']
        password = request.form['passWord']
        password_candidate = sha256_crypt.encrypt(password)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        print(usuario[4])
        print(password_candidate)
        if sha256_crypt.verify(password, usuario[4]):
            firebase2.delete('/Users/{}'.format(username),None)
            cur.execute("UPDATE users set username=%s WHERE username=%s",[novo_username,username])
            cur.execute("UPDATE arquivos SET autor=%s WHERE autor=%s",[novo_username,username])
            conn.commit()
            cur.close()
            sucesso = "Username alterado com sucesso!"
            session['username'] = novo_username
            data = {"Nome":usuario[1],"Username":novo_username,"Email":usuario[3],"Password":usuario[4]}
            firebase2.put('/Users',"{}".format(novo_username),data)
            return render_template('changeusername.html',mensagem_sucesso=sucesso)
        elif len(novo_username) == 0:
            erro = "Username não pode ser vazio!"
            return render_template('changeusername.html',mensagem_erro = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('changeusername.html',mensagem_erro = erro)
        else:
            erro="Login Invalido!"
            return render_template('changeusername.html',mensagem_erro = erro)
    return render_template('changeusername.html')

@app.route('/change-email',methods=["GET","POST"])
@is_logged_in
def Changeemail():
    if request.method == "POST":
        username = session['username']
        novo_email = request.form['newEmail']
        password = request.form['passWord']
        password_candidate = sha256_crypt.encrypt(password)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        if sha256_crypt.verify(password, usuario[4]):
            cur.execute("UPDATE users set email=%s WHERE username=%s",[novo_email,username])
            conn.commit()
            cur.close()
            sucesso = "Email alterado com sucesso!"
            data = {"Nome":usuario[1],"Username":username,"Email":novo_email,"Password":usuario[4]}
            firebase2.put('/Users',"{}".format(username),data)
            return render_template('change-email.html',mensagem_sucesso=sucesso)
        elif len(novo_email) == 0:
            erro = "Email não pode ser vazio!"
            return render_template('change-email.html',mensagem_erro = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('change-email.html',mensagem_erro= erro)
        else:
            erro="Login Invalido!"
            return render_template('change-email.html',mensagem_erro = erro)
    return render_template('change-email.html')

@app.route('/changepassword',methods=["GET","POST"])
@is_logged_in
def Changepassword():
    if request.method == "POST":
        username = session['username']
        novo_password = request.form['newPassword']
        new_pass = sha256_crypt.encrypt(novo_password)
        password = request.form['passWord']
        password_candidate = sha256_crypt.encrypt(password)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        usuario = cur.fetchone()
        if sha256_crypt.verify(password, usuario[4]):
            cur.execute("UPDATE users set password=%s WHERE username=%s",[new_pass,username])
            conn.commit()
            cur.close()
            sucesso = "Senha alterada com sucesso!"
            data = {"Nome":usuario[1],"Username":username,"Email":usuario[3],"Password":new_pass}
            firebase2.put('/Users',"{}".format(username),data)
            return render_template('change-password.html',mensagem_sucesso=sucesso)
        elif len(novo_password) == 0:
            erro = "Nova senha não pode ser vazio!"
            return render_template('change-password.html',mensagem_erro = erro)
        elif len(password) == 0:
            erro = "Senha vazia!"
            return render_template('change-password.html',mensagem_erro = erro)
        else:
            erro="Login Invalido!"
            return render_template('change-password.html',mensagem_erro = erro)
    return render_template('change-password.html')

@app.route('/delete/<int:id>',methods=["GET","POST"])
@is_logged_in
def delete(id):
    cur = conn.cursor()
    username = session['username']
    cur = conn.cursor()
    cur.execute("SELECT * FROM arquivos WHERE id=%s",[id])
    arquivo = cur.fetchone()
    if arquivo[2] == username:
        cur.execute("DELETE FROM arquivos WHERE id=%s",[id])
        conn.commit()
        cur.close()
        return redirect(url_for('menu'))
    else:
        cur.close()
        return redirect(url_for('minha-conta'))

@app.route('/posts-privados')
@is_logged_in
def Postsprivados():
    username = session['username']
    cur = conn.cursor()
    cur.execute("SELECT * FROM arquivos WHERE autor=%s AND publico IS NOT TRUE",[username])
    arquivos_privados=cur.fetchall()
    cur.close()
    return render_template('posts-privados.html',arquivos=arquivos_privados)

@app.route('/tornar-publico/<int:id>')
@is_logged_in
def Tornar_publico(id):
    username = session['username']
    cur = conn.cursor()
    cur.execute("SELECT * FROM arquivos WHERE id=%s",[id])
    arquivo = cur.fetchone()
    if username == arquivo[2]:
        cur.execute("UPDATE arquivos SET publico=true WHERE id=%s",[id])
        cur.execute("UPDATE arquivos SET local=%s WHERE id=%s",["Firebase",id])
        conn.commit()
        cur.close()
        return redirect(url_for('menu'))
    else:
        cur.close()
        return redirect(url_for('minha-conta'))

@app.route('/tornar-privado/<int:id>')
@is_logged_in
def Tornar_privado(id):
    username = session['username']
    cur = conn.cursor()
    cur.execute("SELECT * FROM arquivos WHERE id=%s",[id])
    arquivo = cur.fetchone()
    if username == arquivo[2]:
        cur.execute("UPDATE arquivos SET publico=false WHERE id=%s",[id])
        cur.execute("UPDATE arquivos SET local=%s WHERE id=%s",["Firebase-privado",id])
        conn.commit()
        cur.close()
        return redirect(url_for('menu'))
    else:
        cur.close()
        return redirect(url_for('menu'))


if __name__ == '__main__':
    app.run(debug=True)
