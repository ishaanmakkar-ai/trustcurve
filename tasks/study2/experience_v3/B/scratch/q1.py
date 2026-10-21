from lib import *
for rid in ['2DVZMS','TI7NSI','3FRNFB','Y038F9','NASS9T','AW4ZI0','SI5UKW','QGR999','C94NNS','4CRC2E','JBYKQ0','UB8QZ1','SJWOFH','5UM9G0','7IR32O','1ERWZ8','K2LPTR','900SCC','DB1Y70','F5N7ND','R557QS','OJ56D8','71B2PU','RH5QMP','6E2AQ3','MQS6FV','XEHM4B','34XLFT','0171JI']:
    r=R[rid]
    print(rid,r['user_id'],U[r['user_id']]['membership'],r['cabin'],len(r['passengers']),'->eco',cabin_change_cost(rid,'economy'),'->bus',cabin_change_cost(rid,'business')[0])
