from django.db import models
import config

# Create your models here.
class RltStatus(models.Model):
	relation = models.CharField(max_length = 100, db_index = True)
	status = models.IntegerField(default = 0)
	# status 0: config.STATUS_STOP
	# status 1: config.STATUS_RUNNING
	def __unicode__(self):
		return self.relation + '->' + config.STATUS_DESC[self.status]
