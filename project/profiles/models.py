# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """
    Профайл пользователя
    """
    user            = models.OneToOneField(User, verbose_name=u'Пользователь', related_name='profile')
    is_company      = models.BooleanField(u'Это компания?', default=True)
    is_report       = models.BooleanField(u'Доступ к отчетам?')
    is_super_user   = models.BooleanField(u'Это супер пользователь?')
    is_buh          = models.BooleanField(u'Это бухгалтер')
    telefon         = models.CharField(u'Телефон', max_length=18, blank=True)
    image           = models.ImageField(upload_to='profile_img',blank=True, null=True)

    def __unicode__(self):
        return self.user.first_name

    class Meta:
        verbose_name = u'Профиль'
        verbose_name_plural = u'Профили'
