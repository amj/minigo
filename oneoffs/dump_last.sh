

WORK_DIR=$1

while true; do
LAST=`ls -I '*target*' $WORK_DIR/sgf/eval | tail -n 1`
#LAST=`ls $WORK_DIR/sgf/eval | tail -n 1`

F=`ls $WORK_DIR/sgf/eval/$LAST | grep "\-50\-" - `
if [ ! -f "$WORK_DIR/sgf/eval/$LAST/$F" ]; then
	echo "Waiting for games in $LAST..."
	sleep 20
fi 
python oneoffs/dump_game.py $WORK_DIR/sgf/eval/$LAST/$F
sleep 1
F=`ls $WORK_DIR/sgf/eval/$LAST | grep "\-30\-" - `
python oneoffs/dump_game.py $WORK_DIR/sgf/eval/$LAST/$F
sleep 1
F=`ls $WORK_DIR/sgf/eval/$LAST | grep "\-80\-" - `
python oneoffs/dump_game.py $WORK_DIR/sgf/eval/$LAST/$F
sleep 1
F=`ls $WORK_DIR/sgf/eval/$LAST | grep "\-99\-" - `
python oneoffs/dump_game.py $WORK_DIR/sgf/eval/$LAST/$F

echo $LAST

while : 
do
		NEXT=`ls -I '*target*' $WORK_DIR/sgf/eval | tail -n 1`
		if [ $NEXT != $LAST ] ; then
				break
		fi
		echo "Waiting... Last model seen was $NEXT"
		sleep 15
done
done
