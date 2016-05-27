# coding: utf-8

RMV_LOWER_BOUND = 0.2

def old_readfile(filename):
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

def readfile(filename):

	def getlist(s):
		return map(lambda x: int(x), s.split(',')) if s != '-' else []

	instances = {}
	patterns = {}
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

def write2file(outname, instances, patterns):
	def getstr(l):
		return ','.join(map(lambda x: str(x), l)) if l else '-'

	f = open(outname, 'w')
	f.write('instances\n')
	for i, ins in instances.items():
		f.write('%d\t%s\t%s\t%s\t%f\n' % (i, ins['content'].encode('utf-8'), getstr(ins['from_list']), getstr(ins['to_list']), ins['p']))
	f.write('\npatterns\n')
	for i, pat in patterns.items():
		f.write('%d\t%s\t%s\t%s\t%f\n' % (i, pat['content'].encode('utf-8'), getstr(pat['from_list']), getstr(pat['to_list']), pat['p']))
	f.close()


def rmv(tp, i, instances, patterns):
	assert tp == 'i' or tp == 'p'
	if tp == 'i':
		print('remove instance: %s\n' % instances[i]['content'])
		for j in instances[i]['from_list']:
			patterns[j]['to_list'].remove(i)
		for j in instances[i]['to_list']:
			patterns[j]['from_list'].remove(i)
			patterns[j]['p'] *= len(patterns[j]['from_list']) / (len(patterns[j]['from_list']) + 1.0)
			if patterns[j]['p'] <= RMV_LOWER_BOUND:
				rmv('p', j, instances, patterns)
		instances.pop(i)
	elif tp == 'p':
		print('remove pattern: %s\n' % patterns[i]['content'])
		for j in patterns[i]['from_list']:
			instances[j]['to_list'].remove(i)
		for j in patterns[i]['to_list']:
			instances[j]['from_list'].remove(i)
			instances[j]['p'] *= len(instances[j]['from_list']) / (len(instances[j]['from_list']) + 1.0)
			if instances[j]['p'] <= RMV_LOWER_BOUND:
				rmv('i', j, instances, patterns)
		patterns.pop(i)


def ppg(tp, i, delta, instances, patterns):
	assert tp == 'i' or tp == 'p'
	if tp == 'i':
		instances[i]['p'] += delta
		ppg_list = instances[i]['from_list']
		if instances[i]['p'] > 1.0:
			instances[i]['p'] = 1.0
		if instances[i]['p'] <= RMV_LOWER_BOUND:
			rmv('i', i, instances, patterns)
		if ppg_list and abs(delta / 2 / len(ppg_list)) > 0.0001:
			for j in ppg_list:
				ppg('p', j, delta / 2 / len(ppg_list), instances, patterns)
		
	elif tp == 'p':
		patterns[i]['p'] += delta
		ppg_list = patterns[i]['from_list']
		if patterns[i]['p'] > 1.0:
			patterns[i]['p'] = 1.0
		if patterns[i]['p'] <= RMV_LOWER_BOUND:
			rmv('p', i, instances, patterns)
		if ppg_list and abs(delta / 2 / len(ppg_list)) > 0.0001:
			for j in ppg_list:
				ppg('i', j, delta / 2 / len(ppg_list), instances, patterns)




