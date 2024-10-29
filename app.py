from flask import Flask, render_template, request, redirect, url_for
from models import db, Card
from datetime import datetime, timedelta
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

def update_card_review(card, quality):
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be between 0 and 5.")

    if quality < 3:
        card.interval = 1
        card.review_count = 0
    else:
        card.easiness_factor = card.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cards')
def list_cards():
    cards = Card.query.all()
    return render_template('index.html', cards=cards)

@app.route('/card/<int:card_id>')
def show_card(card_id):
    card = Card.query.get_or_404(card_id)
    return render_template('card.html', card=card)

@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        card_type = request.form['card_type']
        tags = request.form['tags']
        new_card = Card(question=question, answer=answer, card_type=card_type, tags=tags)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('list_cards'))
    return render_template('add_card.html')

@app.route('/review')
def review_cards():
    cards_to_review = Card.query.filter(Card.next_review <= datetime.now()).order_by(Card.next_review).all()
    if cards_to_review:
        card = cards_to_review[0]
        return render_template('review.html', card=card)
    else:
        return "Нет карточек для повторения на сегодня!"

@app.route('/submit_review/<int:card_id>', methods=['POST'])
def submit_review(card_id):
    quality = int(request.form['quality'])
    card = Card.query.get_or_404(card_id)
    update_card_review(card, quality)
    return redirect(url_for('review_cards'))

if __name__ == '__main__':
    app.run(debug=True)
