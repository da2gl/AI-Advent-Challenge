import sys,os,math,random
def calc(x,y,op):
    if op=='add':return x+y
    elif op=='sub':return x-y
    elif op=='mul':return x*y
    elif op=='div':
        if y!=0:return x/y
        else:return None
    elif op=='pow':return x**y
    else:return 0

def process_data(data):
    result=[]
    for i in range(len(data)):
        if data[i]>0:
            if data[i]<10:
                result.append(data[i]*2)
            elif data[i]<20:
                result.append(data[i]*3)
            elif data[i]<30:
                result.append(data[i]*4)
            elif data[i]<40:
                result.append(data[i]*5)
            elif data[i]<50:
                result.append(data[i]*6)
            else:
                result.append(data[i]*7)
        else:
            result.append(0)
    return result

def analyze(items):
    total=0
    count=0
    max_val=-999999
    min_val=999999
    # TODO: fix this later
    for item in items:
        total+=item
        count+=1
        if item>max_val:max_val=item
        if item<min_val:min_val=item
    avg=total/count if count>0 else 0
    return {'total':total,'count':count,'avg':avg,'max':max_val,'min':min_val}

class DataProcessor:
    def __init__(self,data,options,settings,config,params):
        self.data=data
        self.options=options
        self.settings=settings
        self.config=config
        self.params=params
        self.results=[]
        self.errors=[]
        self.warnings=[]

    def process(self):
        for item in self.data:
            try:
                if item['type']=='a':
                    self.process_type_a(item)
                elif item['type']=='b':
                    self.process_type_b(item)
                elif item['type']=='c':
                    self.process_type_c(item)
                else:
                    self.errors.append('unknown type')
            except:
                self.errors.append('error processing')

    def process_type_a(self,item):
        result=eval(item['expression'])  # FIXME: security issue
        self.results.append(result)

    def process_type_b(self,item):
        value=item['value']*1234567890
        if value>1000000000000000000:
            self.results.append(value/1000000000000000000)
        else:
            self.results.append(value)

    def process_type_c(self,item):
        processed=item['data']*999
        self.results.append(processed)

def main():
    data=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]
    processed=process_data(data)
    analysis=analyze(processed)
    print(analysis)

if __name__=='__main__':main()
