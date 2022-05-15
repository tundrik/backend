from django.db import models

RESIDENTIAL = 'residential'
HOUSE = 'house'
GROUND = 'ground'
COMMERCIAL = 'commercial'


class Person(models.Model):
    id = models.AutoField(primary_key=True)
    guid = models.UUIDField()
    pic = models.CharField(max_length=32, default='User')
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    phone = models.PositiveBigIntegerField()
    search_full = models.CharField(max_length=128)
    ranging = models.PositiveIntegerField()

    class Meta:
        abstract = True


class Employee(Person):
    """Таблица Сотрудников"""
    telegram_chat_id = models.PositiveBigIntegerField(null=True)
    role = models.CharField(max_length=16, default='realtor')
    manager = models.ForeignKey('self', related_name='+', null=True, on_delete=models.SET_NULL)
    has_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'employee'


class Customer(Person):
    """Таблица Клиентов"""

    class Meta:
        db_table = 'customer'


class Demand(models.Model):
    """Таблица заявок на покупку и аренду"""
    id = models.AutoField(primary_key=True)
    deal = models.CharField(max_length=16)
    """deal: (bay|rent)"""
    type_enum = models.CharField(max_length=16)
    """type_enum: (residential|house|ground|commercial)"""
    price = models.PositiveIntegerField(default=0)
    price_square = models.PositiveIntegerField(default=0)
    price_square_ground = models.PositiveIntegerField(default=0)
    square = models.PositiveIntegerField(default=0)
    square_ground = models.PositiveIntegerField(default=0)

    comment = models.TextField()
    published = models.PositiveIntegerField()
    ranging = models.PositiveIntegerField()

    employee = models.ForeignKey(Employee, related_name='+', on_delete=models.RESTRICT)
    customer = models.ForeignKey(Customer, related_name='+', on_delete=models.RESTRICT)

    class Meta:
        db_table = 'demand'


class Location(models.Model):
    """Таблица локаций адресов (зданий, участков)"""
    id = models.AutoField(primary_key=True)

    floors = models.PositiveSmallIntegerField(default=0)
    """
    supple JSON: 
            has_closed_area: bool   - закрытая територия
            has_lift: bool          - лифт
            has_rubbish_chute: bool - мусоропровод
            
            ground and house
            has_electricity: bool - электричество
            has_water: bool - водопровод
            has_gas: bool - газ  
            has_sewerage: bool - канализация  
    """
    supple = models.JSONField(default=dict)
    address = models.CharField(max_length=128)
    locality = models.CharField(max_length=32)
    district = models.CharField(max_length=32)
    street = models.CharField(max_length=128)
    street_type = models.CharField(max_length=16)
    house = models.CharField(max_length=16)

    lat = models.CharField(max_length=14)
    lng = models.CharField(max_length=14)

    class Meta:
        db_table = 'location'


class Project(models.Model):
    """Таблица комплексов"""
    id = models.AutoField(primary_key=True)
    mirabase_id = models.CharField(max_length=64)
    type_enum = models.CharField(max_length=8, default="ЖК")
    """type_enum: (ЖК|КП)"""

    project_name = models.CharField(max_length=64, unique=True)
    price = models.PositiveBigIntegerField(default=0)
    square = models.PositiveIntegerField(default=0)
    price_square = models.PositiveIntegerField(default=0)

    comment = models.TextField()

    published = models.PositiveIntegerField()
    ranging = models.PositiveIntegerField()

    location = models.ForeignKey(Location, related_name='+', on_delete=models.RESTRICT)
    employee = models.ForeignKey(Employee, related_name='+', on_delete=models.RESTRICT)

    class Meta:
        db_table = 'project'


class Estate(models.Model):
    """Таблица объектов недвижимости"""
    id = models.AutoField(primary_key=True)
    type_enum = models.CharField(max_length=32)
    """type_enum: (residential|house|ground|commercial)"""
    object_type = models.PositiveIntegerField(default=0)

    price = models.PositiveBigIntegerField(default=0)
    price_square = models.PositiveIntegerField(default=0)
    price_square_ground = models.PositiveIntegerField(default=0)
    square = models.PositiveIntegerField(default=0)
    square_ground = models.PositiveIntegerField(default=0)

    rooms = models.PositiveSmallIntegerField(default=0)
    floor = models.PositiveSmallIntegerField(default=0)

    comment = models.TextField()
    """
    supple JSON: 
            has_last_floor: bool   последний этаж
            renovation: int        ремонт
            walls_type: материал стен
            status: статус участка
    """
    supple = models.JSONField(default=dict)

    has_site = models.BooleanField(default=True)
    has_avito = models.BooleanField(default=False)
    has_yandex = models.BooleanField(default=False)
    has_cian = models.BooleanField(default=False)
    has_domclick = models.BooleanField(default=False)

    published = models.PositiveIntegerField()
    ranging = models.PositiveIntegerField()

    project = models.ForeignKey(Project, related_name='estates', on_delete=models.RESTRICT, null=True)
    location = models.ForeignKey(Location, related_name='estates', on_delete=models.RESTRICT)
    employee = models.ForeignKey(Employee, related_name='+', on_delete=models.RESTRICT)
    customer = models.ForeignKey(Customer, related_name='+', on_delete=models.RESTRICT)

    class Meta:
        db_table = 'estate'


class Media(models.Model):
    id = models.AutoField(primary_key=True)
    type_enum = models.CharField(max_length=32, default='image')
    link = models.CharField(max_length=164)
    ranging = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class ProjectMedia(Media):
    """Таблица медиа комплексов"""
    project = models.ForeignKey(Project, related_name='media', on_delete=models.CASCADE)

    class Meta:
        db_table = 'project_media'


class EstateMedia(Media):
    """Таблица медиа обектов недвижимости"""
    estate = models.ForeignKey(Estate, related_name='media', on_delete=models.CASCADE)

    class Meta:
        db_table = 'estate_media'


class EstateKit(models.Model):
    """Таблица подборок объектов"""
    id = models.AutoField(primary_key=True)
    kit_name = models.CharField(max_length=164)
    employee = models.ForeignKey(Employee, related_name='+', on_delete=models.CASCADE)

    class Meta:
        db_table = 'estate_kit'


class EstateKitMember(models.Model):
    """Таблица участников подборки объектов"""
    id = models.AutoField(primary_key=True)
    kit = models.ForeignKey(EstateKit, related_name='members', on_delete=models.CASCADE)
    estate = models.ForeignKey(Estate, related_name='+', on_delete=models.CASCADE)
    ranging = models.PositiveIntegerField()

    class Meta:
        db_table = 'estate_kit_member'
