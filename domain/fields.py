from django.db import models


class BigForeignKey(models.ForeignKey):
    def db_type(self, connection):
        """
        Добавляет поддержку BIGINT для ForeignKey
        """
        return models.PositiveBigIntegerField().db_type(connection=connection)


class BigOneToOneField(models.OneToOneField):
    def db_type(self, connection):
        """
        Добавляет поддержку BIGINT для OneToOneField
        """
        return models.PositiveBigIntegerField().db_type(connection=connection)
