# coding: utf-8
import subprocess
import re

MIDDLE_UPPER_BOUND = 5
MIDDLE_LOWER_BOUND = 1
E_BOUND = 3		#大于E_BOUND时，只取中间的部分。小于等于时向左、右取。
LEFT_WINDOW = 3	#向左、右取时，固定取窗口大小（若遇到标点则提前停止）
RIGHT_WINDOW = 3
TYPE_MID = 'm'
TYPE_LEFT = 'l'
TYPE_RIGHT = 'r'
digit_pattern = re.compile('\d+')
input_filename = '../output/step3.txt'
output_filename = '../../corpus/relation/candidate.txt'

def check(flag, tp):
	if tp == 'n' or tp == 'noun':
		res = (flag.lower().startswith('/n'))
	elif tp == 'p' or tp == 'punc':
		res = (flag.lower() == '/x')
	elif tp == 'pp' or tp == 'prep':
		res = (flag.lower() == '/p')
	elif tp == 'v' or tp == 'verb':
		res = (flag.lower() == '/v')
	elif tp == 'a' or tp == 'ad':
		res = (flag.lower().startswith('/a'))
	return res

# 把数字换成#，把引号去掉，把·连接的人名变成一个词
def preprocess(segments):
	words = [digit_pattern.sub('#',seg[:seg.rfind('/')]) for seg in segments]
	flags = [seg[seg.rfind('/'):] for seg in segments]
	new_words, new_flags = [], []
	# 要删掉的标点
	rm_punc = ['"', '“'.decode('utf-8'), '”'.decode('utf-8'), '\'', '‘'.decode('utf-8'), '’'.decode('utf-8'), '《'.decode('utf-8'), '》'.decode('utf-8')]
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
		# 合并相邻的名词
		# elif len(new_flags) > 0 and check(new_flags[-1], 'n') and check(flags[i], 'n'):
		# 	new_words[-1] += words[i]
		else:
			new_words.append(words[i])
			new_flags.append(flags[i])
		i += 1
	return new_words, new_flags

def getContext(words):
	if MIDDLE_LOWER_BOUND <= len(words) <= MIDDLE_UPPER_BOUND:
		return ''.join(words)
	else:
		return ''
			

def extractCand(line):
	words, flags = preprocess(line.strip().decode('utf-8').split())
	res = ''
	noun_pos = [i for i in xrange(len(flags)) if check(flags[i], 'n') and len(words[i]) > 1]
	if len(noun_pos) > 1:
		for i in xrange(len(noun_pos)):
			for j in xrange(i + 1, len(noun_pos)):
				hasPunc = False
				for k in xrange(noun_pos[j - 1] + 1, noun_pos[j]):
					if check(flags[k], 'p'):
						hasPunc = True
						break
				if not hasPunc:
					context = getContext(words[noun_pos[i] + 1 : noun_pos[j]])
					if context:
						if len(context) > E_BOUND:
							# res += words[noun_pos[i]] + '!\t' + context  + '\t' + words[noun_pos[j]] + '!\n'
							res += "%s\t%s\t%s\t%s\n" % (words[noun_pos[i]], words[noun_pos[j]], context, TYPE_MID)
						else:
							ii = noun_pos[i] - 1
							while ii >= max(0, noun_pos[i] - LEFT_WINDOW) and not check(flags[ii], 'p'):
								ii -= 1
							if ii + 1 < noun_pos[i]:
								# res += ''.join(words[ii+1: noun_pos[i]]) + '\t' + words[noun_pos[i]] + '!\t' + context + '\t'  + words[noun_pos[j]] + '!\n'
								res += '%s\t%s\t%s\t%s\t%s\n' % (words[noun_pos[i]], words[noun_pos[j]], ''.join(words[ii+1: noun_pos[i]]), context, TYPE_LEFT)
							jj = noun_pos[j] + 1
							while jj < min(len(words), noun_pos[j] + RIGHT_WINDOW + 1) and not check(flags[jj], 'p'):
								jj += 1
							if noun_pos[j] + 1 < jj:
								# res += words[noun_pos[i]] + '!\t' + context + '\t'  + words[noun_pos[j]] + '!\t' + ''.join(words[noun_pos[j]+1: jj]) + '\n'
								res += '%s\t%s\t%s\t%s\t%s\n' % (words[noun_pos[i]], words[noun_pos[j]], context, ''.join(words[noun_pos[j]+1: jj]), TYPE_RIGHT)

				else:
					break
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



