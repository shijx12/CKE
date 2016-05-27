#! /bin/sh
sort ../../corpus/relation/candidate.txt | 
	uniq -c | 
		awk '$1 >= 2 { for (x = 1; x <= NF; x += 1) printf("%s\t", $x); printf("\n")}' |
			sort -nr -k 1 |
				awk '{ for (x = 2; x <= NF; x += 1) printf("%s\t", $x); printf("%s\n", $1)}' > ../../corpus/relation/candidate.count