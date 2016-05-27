# coding:utf-8
from collections import Counter
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


PATTERN_PRECISION_LOWER_BOUND = 0.5
CANDIDATE_LOWER_BOUND = 2
CANDIDATE_WEIGHT = 1
EXCLUSIVE_WEIGHT = -5

class CategoryCPL(object):

	#############################
	# category 	当前的category名称
	# basedir 	所有category所在的目录
	# exclusive_predicates		互斥的category名称
	#############################
	def __init__(self, basedir, category, exclusive_predicates, startfrom = -1):
		self.category 	= category
		self.basedir 	= basedir
		self.directory	= os.path.join(basedir, category)
		# self.iternum 是当前的迭代次数，即 directory 中最新的文件名称。如果 startfrom_0=True ，则iternum初始化为 0
		self.iternum 	= max(map(lambda x: int(x), filter(lambda x: x[0] != '.', os.listdir(self.directory)))) if startfrom == -1 else startfrom
		# self.instance_objects/pattern_objects: 
		# {(id): {
		#	'content': (),
		#	'from_list': [],
		#	'p': ()
		# }}
		self.instance_objects, self.pattern_objects = self.readPredicateFile(os.path.join(self.directory, str(self.iternum)))
		# self.instances/patterns:
		# {'content': (id)}
		self.instances 	= {}
		self.ins_maxid 	= -1
		for i in self.instance_objects.keys():
			self.instances[self.instance_objects[i]['content']] = i
			if i > self.ins_maxid:
				self.ins_maxid = i
		self.patterns 	= {}
		self.pat_maxid 	= -1
		for i in self.pattern_objects.keys():
			self.patterns[self.pattern_objects[i]['content']] = i
			if i > self.pat_maxid:
				self.pat_maxid = i
		
		self.exclusive_predicates = exclusive_predicates
		# 这个的位置可以放到learn函数开头，表示每次迭代都重新读一遍
		# exclusive_instances/patterns 是单纯的list
		self.exclusive_instances, self.exclusive_patterns = self.readExclusiveConstraints()
		self.finished = False
		print 'init for category ' + self.category
		print 'exclusive predicates: ',
		for d in self.exclusive_predicates:
			print d,
		print

	#############################
	# filename：待读取的predicate文件名。
	# 文件格式约定如下："instances"单独占一行，以下每行都是一条instance。中间空一行。"patterns"单独占一行，以下每行都是一条pattern。
	# 每条的格式为：[id]\t[content]\t[from_list]\t[p]\n
	#############################
	def readPredicateFile(self, filename):
		def getlist(s):
			return map(lambda x: int(x), s.split(',')) if s != '-' else []

		patterns = {}
		instances = {}
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
				ls = line.strip().split('\t')
				patterns[int(ls[0])] = {
					'content': ls[1].decode('utf-8'),
					'from_list': getlist(ls[2]),
					'to_list': getlist(ls[3]),
					'p': float(ls[4]),
				}
			elif 'i' == reading:
				ls = line.strip().split('\t')
				instances[int(ls[0])] = {
					'content': ls[1].decode('utf-8'),
					'from_list': getlist(ls[2]),
					'to_list': getlist(ls[3]),
					'p': float(ls[4]),
				}
		return instances, patterns

	###############################
	# 将instances和patterns都按照约定的格式写入到新的文件中，文件名为self.iternum
	###############################
	def writeNewPredicateFile(self):
		def getstr(l):
			return ','.join(map(lambda x: str(x), l)) if l else '-'

		f = open(os.path.join(self.directory, str(self.iternum)), 'w')
		f.write('instances\n')
		for i, ins in self.instance_objects.items():
			f.write('%d\t%s\t%s\t%s\t%f\n' % (i, ins['content'].encode('utf-8'), getstr(ins['from_list']), getstr(ins['to_list']), ins['p']))
		f.write('\npatterns\n')
		for i, pat in self.pattern_objects.items():
			f.write('%d\t%s\t%s\t%s\t%f\n' % (i, pat['content'].encode('utf-8'), getstr(pat['from_list']), getstr(pat['to_list']), pat['p']))
		f.close()

	###############################
	# 读取最新的exclusive instances和exclusive patterns。
	# 只读取其中的content字段，返回两个list
	###############################
	def readExclusiveConstraints(self):
		instances = []
		patterns = []
		for predicate in self.exclusive_predicates:
			directory = os.path.join(self.basedir, predicate)
			newest_file = os.path.join(directory, str(max(map(lambda x: int(x), filter(lambda x: x[0] != '.', os.listdir(directory))))))
			inst, patt = self.readPredicateFile(newest_file)
			instances += [inst[i]['content'] for i in inst]
			patterns += [patt[i]['content'] for i in patt]
		return instances, patterns

	################################
	# corpus：		当前的所有语料，是一个list，其中每个元素都是一个candidate
	# instances_promoted_num： 	要promote的instance的最大数量
	# patterns_promoted_num：	要promote的pattern的最大数量
	# learn函数表示一次迭代过程
	################################
	def learn(self, corpus, instances_promoted_num, patterns_promoted_num):
		# 如果已经结束，即上一轮没有新的promoted，则直接退出
		if self.finished:
			print("----> CPL finished for %s, total iteration number = %d" % (self.category, self.iternum))
			sys.exit()

		print("----> Current number of iteration is %d" % self.iternum)
		inscand = {} 		#instance candidate, 统计跟一个arg co-occur过的属于self.patterns中的不同pattern的数量。注意是不同的！因为语料已经去重了！
		inscand_from = {}	#instance candidate from，记录co-occur过的pattern的id
		patcand = {}		#pattern candidate, 统计跟一个context co-occur过的属于self.instances中的不同instance的数量。
		patcand_from = {}	#pattern candidate from，记录co-occur过的instance的id
		for each in corpus:
			arg, context, num = each[0], each[1] + '|' + each[2], int(each[3])
			if arg not in self.instances:
				if context in self.patterns: #这里使用patterns还是promoted_patterns，是等价的。前者花时间，后者则要维护每个arg与patterns co-occur的次数
					if arg not in inscand:
						inscand[arg] = CANDIDATE_WEIGHT
						inscand_from[arg] = [self.patterns[context]]
					else:
						inscand[arg] += CANDIDATE_WEIGHT
						inscand_from[arg] += [self.patterns[context]]
				if context in self.exclusive_patterns:
					if arg not in inscand:
						inscand[arg] = EXCLUSIVE_WEIGHT
					else:
						inscand[arg] += EXCLUSIVE_WEIGHT

			if context not in self.patterns:
				if arg in self.instances: #这里使用instances还是promoted_instances，是等价的。前者要多花时间，后者需要多维护一个map
					if context not in patcand:
						patcand[context] = CANDIDATE_WEIGHT
						patcand_from[context] = [self.instances[arg]]
					else:
						patcand[context] += CANDIDATE_WEIGHT
						patcand_from[context] += [self.instances[arg]]
				if arg in self.exclusive_instances:
					if context not in patcand:
						patcand[context] = EXCLUSIVE_WEIGHT
					else:
						patcand[context] += EXCLUSIVE_WEIGHT
		# inscand的排序依据为刚刚统计过的值，值越大则排名越靠前。值若小于等于0则认为违背了constraint。
		# patcand的排序依据为precision，即对于一个pattern，要统计它一共出现了多少次，与self.instances co-occur了多少次。前提是值>0。
		pattern_count = {}
		pattern_correct = {}
		for each in corpus:
			arg, context, num = each[0], each[1] + '|' + each[2], int(each[3])
			if context in patcand and CANDIDATE_LOWER_BOUND <= patcand[context]:
				# 如果context在patcand中，则要对它的precision进行统计。首先统计该context出现的总次数。
				if context in pattern_count:
					pattern_count[context] += 1
				else:
					pattern_count[context] = 1
				# 然后统计该context与self.instances co-occur的次数
				if arg in self.instances:
					if context in pattern_correct:
						pattern_correct[context] += 1
					else:
						pattern_correct[context] = 1
		# 计算pattern_precision
		pattern_precision = {}
		for context in pattern_correct.keys():
			pattern_precision[context] = float(pattern_correct[context]) / pattern_count[context]
		# 得到ranking结果，得到即将进行promote的instance list和pattern list。
		promoted_instances = [x[0] for x in Counter(inscand).most_common() if CANDIDATE_LOWER_BOUND <= x[1]][:instances_promoted_num]
		promoted_patterns = [x[0] for x in Counter(pattern_precision).most_common() if PATTERN_PRECISION_LOWER_BOUND < x[1] < 1.0][:patterns_promoted_num] # 这里非常关键的，不能选择precision为1的pattern，因为这些pattern得不到任何新的instance了！

		# 如果两个promoted list都为空，表明迭代已经可以结束，此时不再生成新的文件。
		if not promoted_instances and not promoted_patterns:
			self.finished = True
		# 否则更新self.instances和self.patterns，将所有的instances和patterns都按照约定的格式写入到新的文件中，文件名为iternum。
		else:
			self.iternum += 1
			print("     The number of promoted instances = %d\n     The number of promoted patterns = %d\n" % (len(promoted_instances), len(promoted_patterns)))
			for ins in promoted_instances:
				self.ins_maxid += 1
				self.instance_objects[self.ins_maxid] = {
					'content': ins,
					'from_list': list(set(inscand_from[ins])),
					'to_list': [],
					'p': 1 - 0.5 ** (len(inscand_from[ins]))
				}
				self.instances[ins] = self.ins_maxid
				for i in inscand_from[ins]:	# 对于ins的from_list中的每一个pattern，将当前ins的id加入到其to_list中
					self.pattern_objects[i]['to_list'].append(self.ins_maxid)

			for pat in promoted_patterns:
				self.pat_maxid += 1
				self.pattern_objects[self.pat_maxid] = {
					'content': pat,
					'from_list': list(set(patcand_from[pat])),
					'to_list': [],
					'p': pattern_precision[pat]
				}
				self.patterns[pat] = self.pat_maxid
				for i in patcand_from[pat]:
					self.instance_objects[i]['to_list'].append(self.pat_maxid)

			self.writeNewPredicateFile()

if __name__ == '__main__':

	INSTANCES_PROMOTED_NUM = 100
	PATTERNS_PROMOTED_NUM = 5
	CORPUS_FILENAME = '../candidate3.counted.txt'
	try:
		cpl = CategoryCPL('../data/category/', '国家', [])
		corpus = [line.strip().decode('utf-8').split() for line in open(CORPUS_FILENAME, 'r')]
		print("Finish reading corpus: %s" % CORPUS_FILENAME)
		for i in xrange(20):
			cpl.learn(corpus, INSTANCES_PROMOTED_NUM, PATTERNS_PROMOTED_NUM)
	except Exception, e:
		print e
	finally:
		pass






