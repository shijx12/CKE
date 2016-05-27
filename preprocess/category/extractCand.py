# coding:utf-8
import subprocess
import re

WINDOW_UPPER_BOUND = 7
WINDOW_LOWER_BOUND = 2
TYPE_BEFORE = 'b' 		#表示arg在context之前
TYPE_AFTER 	= 'a' 		#表示arg在context之后
digit_pattern = re.compile('\d+')
input_filename = '../output/step3.txt'
output_filename = '../../corpus/category/candidate.txt'
classes_filename = '../../corpus/category/sameclasses.txt'

def check(flag, tp):
	if tp == 'n' or tp == 'noun':
		res = (flag.lower().startswith('/n'))
	elif tp == 'p' or tp == 'punc':
		res = (flag.lower() == '/x')
	elif tp == 'pp' or tp == 'prep':
		res = (flag.lower() == '/p')
	elif tp == 'v' or tp == 'verb':
		res = (flag.lower().startswith('/v'))
	elif tp == 'a' or tp == 'ad':
		res = (flag.lower().startswith('/a'))
	elif tp == 'u':
		res = (flag.lower().startswith('/u'))
	return res


sameclasses = []
def findCoordination(words, tags):
	global sameclasses
	pausemark = map(lambda x: x.decode('utf-8'), ['、', '和', '以及', '及'])
	adding = False
	oneclass = []
	i = 0
	while i < len(words)-2:
		if check(tags[i], 'n') and words[i+1] in pausemark:
			if adding:
				oneclass.append(words[i])
			else:
				oneclass = [words[i]]
				adding = True
		elif words[i] in pausemark and check(tags[i+1], 'n'):
			if adding:
				oneclass.append(words[i+1])
			else:
				oneclass = [words[i+1]]
				adding = True
			i += 1
		else:
			adding = False
			oneclass = frozenset(oneclass)
			if len(oneclass) > 1:
				sameclasses.append(oneclass)
		i += 1


# 把引号去掉，把·连接的人名变成一个词
def preprocess(segments):
	words = [seg[:seg.rfind('/')] for seg in segments]
	flags = [seg[seg.rfind('/'):] for seg in segments]
	new_words, new_flags = [], []
	# 要删掉的标点
	rm_punc = ['"', '“'.decode('utf-8'), '”'.decode('utf-8'), '\'', '‘'.decode('utf-8'), '’'.decode('utf-8'), '[', ']']
	# 要强制改flag的词
	rp_map = {
		'的'.decode('utf-8'): '/uj',
		'并'.decode('utf-8'): '/c',
	}
	i = 0
	while i < len(words):
		# 强行修改rp_map中的词对应的flag
		if words[i] in rp_map:
			flags[i] = rp_map[words[i]]
		# 删掉rm_punc中的标点
		if words[i] in rm_punc:
			pass
		# 合并人名
		elif words[i] == '·'.decode('utf-8') and i > 0 and i < (len(words)-1) and check(flags[i-1], 'n') and check(flags[i+1], 'n'):
			new_words[-1] += '·'.decode('utf-8') + words[i+1]
			i += 1
		else:
			new_words.append(words[i])
			new_flags.append(flags[i])
		i += 1
	findCoordination(new_words, new_flags)
	return new_words, new_flags

def getContext(words):
	res = ''
	if WINDOW_LOWER_BOUND <= len(words) <= WINDOW_UPPER_BOUND:
		res = ''.join(words)
	if len(res) <= 1:	#context的长度不能小于等于1
		return ''
	else:
		return res

keep_punc = ['《'.decode('utf-8'), '》'.decode('utf-8'), ',', '.', '，'.decode('utf-8')]

def getPrecedingContext(words, flags):
	contexts = []
	for i in xrange(len(words)-1, max(-1, len(words)-1-WINDOW_UPPER_BOUND), -1):
		# 向前找到标点，标点不含在window中
		if check(flags[i], 'p'):
			context = getContext(words[i+1:])
			if context:
				contexts.append(context)
			if words[i] not in keep_punc:
				break
		# 向前找到动词
		if check(flags[i], 'v'):
			# 在动词前面再包含一个名词，但再往前的一个词不能是介词
			if i >= 1 and check(flags[i - 1], 'n') and (i == 1 or (i > 1 and not check(flags[i - 2], 'pp'))):
				context = getContext(words[i - 1:])
				if context:
					contexts.append(context)
			context = getContext(words[i:])
			if context:
				contexts.append(context)
	return contexts

def getFollowingContext(words, flags):
	contexts = []
	for i in xrange(0, min(len(words), WINDOW_UPPER_BOUND)):
		# 向后找到名词
		if check(flags[i], 'n'):
			context = getContext(words[:i + 1])
			if context:
				contexts.append(context)
		# 向后找到标点
		elif check(flags[i], 'p'):
			context = getContext(words[:i])
			if context:
				contexts.append(context)
			# 如果标点是句号则退出
			if words[i] not in keep_punc:
				break
	return contexts

def extractCand(line):
	words, flags = preprocess(line.strip().decode('utf-8').split())
	res = ''
	for i in xrange(len(words)):
		# 保证名词的长度大于1
		if check(flags[i], 'n') and len(words[i]) > 1:
			contexts = getPrecedingContext(words[:i], flags[:i])
			for context in contexts:
				# res += context + '\t' + words[i] + '\n'
				res += words[i] + '\t' + context + '\t' + TYPE_AFTER + '\n'
			contexts = getFollowingContext(words[i+1:], flags[i+1:])
			for context in contexts:
				# res += words[i] + '\t' + context + '\n'
				res += words[i] + '\t' + context + '\t' + TYPE_BEFORE + '\n'
	return res

if __name__ == '__main__':
	line_total = int(subprocess.Popen(['wc','-l',input_filename],stdout=subprocess.PIPE).stdout.read().split()[0])
	line_count = 0
	output = open(output_filename, 'w')
	for line in open(input_filename, 'r'):
		cand = extractCand(line)
		# if cand:
		# 	print cand
		# 	pause = raw_input()
		line_count += 1
		if line_count % 10000 == 0:
			print 100.0 * line_count / line_total, '%'
		output.write(cand.encode('utf-8'))
	output.close()

	output = open(classes_filename, 'w')
	for oneclass in set(sameclasses):
		for word in oneclass:
			output.write(word.encode('utf-8') + '\t')
		output.write('\n')
	output.close()




