import random
from django.core.management.base import BaseCommand
from faker import Faker
from products.models import Product, Category

class Command(BaseCommand):
    help = "Generates test products in the database"

    def handle(self, *args, **kwargs):
        fake = Faker()
        categories = ["Electronics", "Clothing", "Books", "Furniture", "Toys"]

        # Створення категорій, якщо вони ще не існують
        category_objs = [Category.objects.get_or_create(name=cat)[0] for cat in categories]

        # Створення 50 випадкових товарів
        Product.objects.all().delete()
        for _ in range(50):
            Product.objects.create(
                name=fake.word().capitalize(),  # fake.lexify(text="??????-Gadget", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                description=fake.text(max_nb_chars=100),
                price=random.randint(100, 5000),
                discount_price=random.choice([None, random.randint(50, 4000)]),
                stock=random.randint(0, 100),
                available=random.choice([True, False]),
                sku=fake.unique.uuid4(),
                category=random.choice(category_objs),
                rating=round(random.uniform(1.0, 5.0), 1),
                attributes={"color": fake.color_name(), "size": random.choice(["S", "M", "L", "XL"])},
                image_url = f"https://picsum.photos/id/{random.randint(1, 1000)}/400/400"
            )

        self.stdout.write(self.style.SUCCESS('✅ 50 test products added successfully!'))
