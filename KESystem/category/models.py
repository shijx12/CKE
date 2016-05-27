from django.db import models
import config

# Create your models here.
class CtgStatus(models.Model):
	category = models.CharField(max_length = 100, db_index = True)
	status = models.IntegerField(default = 0)
	# status 0: config.STATUS_STOP
	# status 1: config.STATUS_RUNNING
	exclusions = models.ManyToManyField('self', blank=True)
	def __unicode__(self):
		return self.category + '->' + config.STATUS_DESC[self.status]
