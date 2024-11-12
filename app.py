from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Card
from datetime import datetime, timedelta
from flask_migrate import Migrate
import os
import dotenv
from werkzeug.utils import secure_filename

dotenv.load_dotenv()

# Images from cards
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


# Create a new Flask application instance
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cards.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.secret_key = os.getenv("SECRET_KEY")  # Для flash сообщений

db.init_app(app)
# Initialize Flask-Migrate for handling database migrations
migrate = Migrate(app, db)


# Checks if file what you want to add into the card is allowed(picture)
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def update_card_review(card, quality):
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be between 0 and 5.")

    if quality < 3:
        card.interval = 1
        card.review_count = 0
    else:
        card.easiness_factor = card.easiness_factor + (
            0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        if card.easiness_factor < 1.3:
            card.easiness_factor = 1.3

        if card.review_count == 0:
            card.interval = 1
        elif card.review_count == 1:
            card.interval = 6
        else:
            card.interval = int(card.interval * card.easiness_factor)

        card.review_count += 1

    card.next_review = datetime.now() + timedelta(days=card.interval)
    card.last_reviewed = datetime.now()
    db.session.commit()


# Route to the home page
@app.route("/")
def index():
    return render_template("index.html")


# Route to list all cards
@app.route("/cards")
def list_cards():
    cards = Card.query.order_by(Card.next_review).all()
    return render_template("card_list.html", cards=cards)


@app.route("/card/<int:card_id>")
def show_card(card_id):
    card = Card.query.get_or_404(card_id)
    return render_template("card.html", card=card)


@app.route("/add_card", methods=["GET", "POST"])
def add_card():
    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"]
        card_type = request.form["card_type"]
        tags = request.form["tags"]

        new_card = Card(
            question=question, answer=answer, card_type=card_type, tags=tags
        )

        # Обработка загрузки изображений
        if "question_image" in request.files:
            file = request.files["question_image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                new_card.question += (
                    f'<img src="/{app.config["UPLOAD_FOLDER"]}/{filename}" alt="Image">'
                )

        if "answer_image" in request.files:
            file = request.files["answer_image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                new_card.answer += (
                    f'<img src="/{app.config["UPLOAD_FOLDER"]}/{filename}" alt="Image">'
                )

        db.session.add(new_card)
        db.session.commit()
        flash("Карточка успешно добавлена!", "success")
        return redirect(url_for("list_cards"))
    return render_template("add_card.html")


# adding card
@app.route("/edit_card/<int:card_id>", methods=["GET", "POST"])
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    if request.method == "POST":
        card.question = request.form["question"]
        card.answer = request.form["answer"]
        card.card_type = request.form["card_type"]
        card.tags = request.form["tags"]

        if "question_image" in request.files:
            file = request.files["question_image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                card.question += (
                    f'<img src="/{app.config["UPLOAD_FOLDER"]}/{filename}" alt="Image">'
                )

        if "answer_image" in request.files:
            file = request.files["answer_image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                card.answer += (
                    f'<img src="/{app.config["UPLOAD_FOLDER"]}/{filename}" alt="Image">'
                )

        db.session.commit()

        # flash message
        flash("Карточка успешно обновлена!", "success")
        return redirect(url_for("list_cards"))
    return render_template("edit_card.html", card=card)


@app.route("/review")
def review_cards():
    mode = request.args.get("mode", "flash")  # По умолчанию flash режим
    cards_to_review = (
        Card.query.filter(Card.next_review <= datetime.now())
        .order_by(Card.next_review)
        .all()
    )
    if not cards_to_review:
        return "Нет карточек для повторения на сегодня!"

    card = cards_to_review[0]
    return render_template("review.html", card=card, mode=mode)


@app.route("/submit_review/<int:card_id>", methods=["POST"])
def submit_review(card_id):
    quality = int(request.form["quality"])
    card = Card.query.get_or_404(card_id)
    update_card_review(card, quality)
    return redirect(url_for("review_cards"))


if __name__ == "__main__":
    app.run(debug=True)
