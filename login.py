from flask import Flask, request, render_template_string, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 仮のユーザーデータベース
users = {"test@example.com": "password123"}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email in users and users[email] == password:
            flash("ログイン成功！", "success")
            return redirect(url_for("supermarket"))  # ここを変更
        else:
            flash("メールアドレスまたはパスワードが間違っています。", "danger")

    return render_template_string(open("login.html").read())


@app.route("/supermarket")
def supermarket():
    return render_template_string(open("supermarket.html").read())


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"
db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))
    product_id = db.Column(db.String(10))
    name = db.Column(db.String(50))
    price = db.Column(db.String(10))
    stock = db.Column(db.Integer)




@app.route("/products/<int:product_id>")
def product_detail(product_id):
    products = Product.query.get(product_id)
    if not products:
        return "商品が見つかりません", 404
    return render_template_string(open("product_detail.html").read(), product=products)


@app.route("/products")
def products_list():
    category = request.args.get("category")
    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    return render_template_string(open("products.html").read(), products=products)


if __name__ == "__main__":
    app.run(debug=True)
