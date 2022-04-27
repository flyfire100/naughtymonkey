#! /bin/bash


NAUGHTYMONKEY_SERVER="10.31.30.110"
NAUGHTYMONKEY_PORTT="8080"


start(){
   EXISTS=$( iptables -t nat -L | grep "dpt:$1" | wc -l )
   if (( $EXISTS > 0 ));then
       echo "port have already exist"
       exit 0
   fi
   echo 1 > /proc/sys/net/ipv4/ip_forward
   iptables -t nat -A PREROUTING  ! -s $NAUGHTYMONKEY_SERVER   -p tcp  --dport $1  -j DNAT --to-destination $NAUGHTYMONKEY_SERVER:$NAUGHTYMONKEY_PORTT
   iptables -t nat -A POSTROUTING -j MASQUERADE
}


stop(){
   iptables -t nat -D PREROUTING ! -s $NAUGHTYMONKEY_SERVER   -p tcp  --dport $1  -j DNAT --to-destination $NAUGHTYMONKEY_SERVER:$NAUGHTYMONKEY_PORTT
}



if (( $# != 2  ));then
    echo "usage: $0 start/stop monitor_port"
    exit -1
fi



if [ "$(whoami)" != "root"  ];then
   echo "please user root executurate $0"
    exit -1
fi


case $1 in
    start) start $2;;
    stop) stop $2;;
    *) echo "usage: $0 start/stop monitor_port";;
esac

exit 0
