# coding:utf-8
from collections import Counter
import os
from relation import config
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from django.conf import settings
settings.configure(
    INSTALLED_APPS = (
        'relation',
    ),
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3'),
        }
    },
    TIME_ZONE = 'Asia/Shanghai',
    USE_TZ = True,
)
import django
django.setup()
from relation.models import RltStatus

class RelationCPL(object):

	#############################
	# relation 	当前的relation名称
	# directory： 	当前的relation对应的directory
	# adir
	# bdir
	#############################
	def __init__(self, basedir, relation, adir, bdir):
		self.relation = relation
		self.directory = os.path.join(basedir, relation)
		self.adir = adir
		self.bdir = bdir
		# 读取type constraints，可以放在learn开头，每轮迭代都重新读取一次
		self.readABList()
		# self.iternum是当前的迭代次数，即directory中最新的文件名称
		self.iternum = max(map(lambda x: int(x), filter(lambda x: x[0] != '.', os.listdir(directory))))
		# relation的instance和pattern都是有多个字段的，字段之间统一用 \t 来连接
		self.instances, self.patterns = self.readPredicateFile(os.path.join(directory, str(self.iternum)))
		self.finished = False
		print 'init for relation ' + self.relation

	#############################
	# filename：待读取的predicate文件名。
	# 文件格式约定如下："instances"单独占一行，以下每行都是一条instance。中间空一行。"patterns"单独占一行，以下每行都是一条pattern，每条pattern都以a或b结尾，表示两个arg的顺序。
	# 返回值依次为instance list和pattern list。
	#############################
	def readPredicateFile(self, filename):
		patterns = []
		instances = []
		reading = ''
		for line in open(filename, 'r'):
			if 'patterns' == line.strip().lower():
				reading = 'p'
				continue
			elif 'instances' == line.strip().lower():
				reading = 'i'
				continue
			elif not line.strip():
				continue
			if 'p' == reading:
				patterns.append(line.strip().decode('utf-8'))
			elif 'i' == reading:
				instances.append(line.strip().decode('utf-8'))
		return instances, patterns

	###############################
	# 将instances和patterns都按照约定的格式写入到新的文件中，文件名为self.iternum
	###############################
	def writeNewPredicateFile(self):
		output = open(os.path.join(self.directory, str(self.iternum)), 'w')
		output.write('instances\n')
		for inst in self.instances:
			output.write(inst.encode('utf-8') + '\n')
		output.write('\n')
		output.write('patterns\n')
		for patt in self.patterns:
			output.write(patt.encode('utf-8') + '\n')
		output.close()

	###############################
	# 读取最新的alist和blist(即adir和bdir中最新的instances)
	###############################
	def readABList(self):
		self.alist, self.blist = [], []
		if self.adir:
			self.alist, patt = self.readPredicateFile(os.path.join(self.adir, str(max(map(lambda x: int(x), filter(lambda x: x[0] != '.', os.listdir(self.adir)))))))
		if self.bdir:
			self.blist, patt = self.readPredicateFile(os.path.join(self.bdir, str(max(map(lambda x: int(x), filter(lambda x: x[0] != '.', os.listdir(self.bdir)))))))

	###############################
	# 判断是否满足type constraints
	###############################
	def typeCheck(self, arg):
		# return arg.split()[0] in self.alist and arg.split()[1] in self.blist
		return True

	################################
	# corpus：		当前的所有语料，是一个list，其中每个元素都是一个candidate
	# instances_promoted_num： 	要promote的instance的最大数量
	# patterns_promoted_num：	要promote的pattern的最大数量
	# learn函数表示一次迭代过程
	################################
	def learn(self, corpus, instances_promoted_num, patterns_promoted_num):
		# 如果已经结束，即上一轮没有新的promoted，则直接退出
		if self.finished:
			print("----> CPL finished for %s, total iteration number = %d" % (self.relation, self.iternum))
			return False

		print("----> Current number of iteration is %d" % self.iternum)
		instance_candidate = {} #统计跟一个arg co-occur过的属于self.patterns中的不同pattern的数量。注意是不同的！因为语料已经去重了！
		pattern_candidate = {}	#统计跟一个context co-occur过的属于self.instances中的不同instance的数量。
		for each in corpus:
			arga, argb, context, num = each[0], each[1], '\t'.join(each[2:-1]), int(each[-1])
			arg = arga+'\t'+argb
			if arg not in self.instances and self.typeCheck(arg):
				if (context+'\t'+config.A_BEFORE_B) in self.patterns:
					if arg not in instance_candidate:
						instance_candidate[arg] = config.CANDIDATE_WEIGHT
					else:
						instance_candidate[arg] += config.CANDIDATE_WEIGHT
			arg = argb+'\t'+arga
			if arg not in self.instances and self.typeCheck(arg):
				if (context+'\t'+config.B_BEFORE_A) in self.patterns:
					if arg not in instance_candidate:
						instance_candidate[arg] = config.CANDIDATE_WEIGHT
					else:
						instance_candidate[arg] += config.CANDIDATE_WEIGHT
			con = context+'\t'+config.A_BEFORE_B
			if con not in self.patterns:
				if (arga+'\t'+argb) in self.instances:
					if con not in pattern_candidate:
						pattern_candidate[con] = config.CANDIDATE_WEIGHT
					else:
						pattern_candidate[con] += config.CANDIDATE_WEIGHT
			con = context+'\t'+config.B_BEFORE_A
			if con not in self.patterns:
				if (argb+'\t'+arga) in self.instances:
					if con not in pattern_candidate:
						pattern_candidate[con] = config.CANDIDATE_WEIGHT
					else:
						pattern_candidate[con] += config.CANDIDATE_WEIGHT
		# instance_candidate的排序依据为刚刚统计过的值，值越大则排名越靠前，且值不能小于下界。
		# pattern_candidate的排序依据为precision，即对于一个pattern，要统计它一共出现了多少次，与self.instances co-occur了多少次。前提是值>0。
		pattern_count = {}
		pattern_correct = {}
		for each in corpus:
			arga, argb, context, num = each[0], each[1], '\t'.join(each[2:-1]), int(each[-1])
			con = context+'\t'+config.A_BEFORE_B
			if con in pattern_candidate and config.CANDIDATE_LOWER_BOUND <= pattern_candidate[con]:
				# 如果con在pattern_candidate中，则要对它的precision进行统计。首先统计该con出现的总次数。
				if con in pattern_count:
					pattern_count[con] += 1
				else:
					pattern_count[con] = 1
				# 然后统计该con与self.instances co-occur的次数
				if (arga+'\t'+argb) in self.instances:
					if con in pattern_correct:
						pattern_correct[con] += 1
					else:
						pattern_correct[con] = 1
			con = context+'\t'+config.B_BEFORE_A
			if con in pattern_candidate and config.CANDIDATE_LOWER_BOUND <= pattern_candidate[con]:
				# 如果con在pattern_candidate中，则要对它的precision进行统计。首先统计该con出现的总次数。
				if con in pattern_count:
					pattern_count[con] += 1
				else:
					pattern_count[con] = 1
				# 然后统计该con与self.instances co-occur的次数
				if (argb+'\t'+arga) in self.instances:
					if con in pattern_correct:
						pattern_correct[con] += 1
					else:
						pattern_correct[con] = 1
		# 算出pattern_precision。
		pattern_precision = {}
		for con in pattern_correct.keys():
			pattern_precision[con] = float(pattern_correct[con]) / pattern_count[con]
		# 得到ranking结果，得到即将进行promote的instance list和pattern list。
		promoted_instances = [x[0] for x in Counter(instance_candidate).most_common() if config.CANDIDATE_LOWER_BOUND <= x[1]][:instances_promoted_num]
		promoted_patterns = [x[0] for x in Counter(pattern_precision).most_common() if config.PATTERN_PRECISION_LOWER_BOUND < x[1] < 1.0][:patterns_promoted_num] # 这里非常关键的，不能选择precision为1的pattern，因为这些pattern得不到任何新的instance了！

		# 如果两个promoted list都为空，表明迭代已经可以结束，此时不再生成新的文件。
		if not promoted_instances and not promoted_patterns:
			self.finished = True
		# 否则更新self.instances和self.patterns，将所有的instances和patterns都按照约定的格式写入到新的文件中，文件名为iternum。
		else:
			self.iternum += 1
			print("     The number of promoted instances = %d\n     The number of promoted patterns = %d\n" % (len(promoted_instances), len(promoted_patterns)))
			self.instances += promoted_instances
			self.patterns += promoted_patterns
			self.writeNewPredicateFile()
		return True


def cplmain(relation, iternum):
        
    rltstatus = RltStatus.objects.get(relation = relation)
    if not rltstatus:
        print 'The relation %s does not exist in DB!' % relation
        return
    else:
        if rltstatus.status == config.STATUS_RUNNING:
            print 'The relation %s is running!' % relation
            return
        try:
            rltstatus.status = config.STATUS_RUNNING
            rltstatus.save()
            print 'Status of %s is set to RUNNING! Iternum is %d.' % (relation, iternum)

            cpl = RelationCPL(config.RELATION_BASEDIR, relation, '', '')
            # corpus = []
            corpus = [line.strip().decode('utf-8').split() for line in open(config.CORPUS_FILENAME)]
            print("Finish reading corpus: %s" % config.CORPUS_FILENAME)

            for i in xrange(iternum):
                cont = cpl.learn(corpus, config.INSTANCES_PROMOTED_NUM, config.PATTERNS_PROMOTED_NUM)
                if not cont:
                    break
        except Exception, e:
            print e
        finally:
            rltstatus.status = config.STATUS_STOP
            rltstatus.save()
            print 'Status of %s is set to STOP and CPL finished.' % relation


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: ./RelationCPL.py <relation> <iteration number>"
    else:
        cplmain(sys.argv[1], int(sys.argv[2]))





