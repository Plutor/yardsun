#!/bin/bash

DIR=$( dirname $0 )
DAY=$1

if [[ ! -d "$DIR/photos" ]]; then
  echo "$DIR/photos does not exist"
  exit
fi

if [[ "$DAY" == "" ]]; then
  echo "Usage: mksummary.sh [YYYYMMDD]"
  DAY=$( date +%Y%m%d )
  echo "Using today ($DAY)"
fi

if [[ ! -d "$DIR/photos/$DAY" ]]; then
  echo "$DIR/photos/$DAY does not exist"
  exit
fi

DAY="$DIR/photos/$DAY"
TMP="$DIR/photos/mksummary"

rm -rf $TMP
mkdir $TMP

echo "Making average"
convert "$DAY/??????.png" -evaluate-sequence mean "$DAY/average.png"

NUMLAY=$( ls $DAY/??????-scaled.jpg | wc -l )
N=1
for F in $DAY/??????-scaled.jpg; do
  printf "\rMaking layers $N/$NUMLAY"
  OUT=$( basename $F )
  montage $F "$DAY/average.png" -mode Concatenate -gravity south "$TMP/$OUT"
  N=$((N+1))
done
echo

echo "Making animated summary"
convert $TMP/*.jpg -delay 5 -gravity southwest -crop 762x800+0-0 +repage $DAY/summary.gif

echo "Done"
