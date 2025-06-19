#!/usr/bin/awk -f

BEGIN {
  outfile = ARGV[1]
  ARGC--
}
{ a[NR] = $0 }
END {
  for(i=1;i<=NR;i++)
    print a[i] > outfile
}
