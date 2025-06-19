#!/usr/bin/awk -f

# This script replaces the sponge programm from the [moreutils package](https://joeyh.name/code/moreutils/).
# The sponge soaks up standard input and writes it to a file.
# This is useful for working with jq to write jq's output back to the original file.
# An alternative to using this script would be to use temporary file, for example:
# cp file.json file.json.tmp &&
# jq . file.json.tmp >file.json &&
# rm file.json.tmp

BEGIN {
  outfile = ARGV[1]
  ARGC--
}
{ a[NR] = $0 }
END {
  for(i=1;i<=NR;i++)
    print a[i] > outfile
}
