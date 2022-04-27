nohup mitmdump -q -s monkey.py --set block_global=false  > /dev/null 2>&1 &
nohup python monkey_client.py  > /dev/null 2>&1 &
