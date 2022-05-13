from .HslCommunication import SiemensS7Net
from .HslCommunication import SiemensPLCS
from .HslCommunication import SoftBasic


def printReadResult(result, addr):
    if result.IsSuccess:
        print("success[" + addr + "]   " + str(result.Content))
    else:
        print("failed[" + addr + "]   "+result.Message)
def printWriteResult(result, addr):
    if result.IsSuccess:
        print("success[" + addr + "]")
    else:
        print("falied[" + addr + "]  " + result.Message)


if __name__ == "__main__":
    siemens = SiemensS7Net(SiemensPLCS.S300, "192.168.0.173")
    if siemens.ConnectServer().IsSuccess == False:
        print("connect falied")
    else:
        # read block
        # print("connect succeed!")
        # read = siemens.Read('M630',6)
        # if read.IsSuccess:
            # m100_0 = read.Content[0]
            # m100_1 = read.Content[1]
            # m100_2 = read.Content[2]
            # m100_3 = read.Content[3]
            # m100_4 = read.Content[4]
            # m100_5 = read.Content[5]
            # print m100_0,m100_1,m100_2,m100_3,m100_4,m100_5
            # print(read)
        # else:
        #     print(read.Message)


        for i in range(0, 200):
            addrtmp = 'M%d' % i + '.0'
            readContent = siemens.Read(addrtmp,10).Content
            boolArray = HslCommunication.BasicFramework.SoftBasic.ByteToBoolArray(readContent, readContent.Length * 8)
            print boolArray
        # read = siemens.ReadBool('M103.0').Content
        print siemens.ReadByte('M63.1').Content
        siemens.ConnectClose()