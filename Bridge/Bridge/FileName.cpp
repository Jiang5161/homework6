#include <iostream>
#include <string>
#include <map>
#include <vector>
#include <iomanip>

using namespace std;

// 定义广播地址
const string BROADCAST_ADDR = "F";

// 定义帧结构
struct Frame {
    string srcAddr;   // 源地址
    int srcPort;      // 源端口 (1 或 2)
    string destAddr;  // 目的地址
};

// 网桥类
class Bridge {
private:
    // MAC地址表：Key是MAC地址，Value是端口号
    map<string, int> macTable;

public:
    // 处理帧的函数
    void processFrame(const Frame& frame) {
        cout << "--------------------------------" << endl;
        cout << "处理帧: [源: " << frame.srcAddr
            << ", 源端口: " << frame.srcPort
            << ", 目的: " << frame.destAddr << "]" << endl;

        // --- 第一步：自学习 (检查源地址) ---
        // 如果表中没有该源地址，或者端口发生了变化，则更新表
        if (macTable.find(frame.srcAddr) == macTable.end()) {
            macTable[frame.srcAddr] = frame.srcPort;
            cout << "学习: 添加/更新地址 " << frame.srcAddr
                << " 到端口 " << frame.srcPort << endl;
        }

        // --- 第二步：转发决策 (检查目的地址) ---
        int destPort = -1; // -1 表示未知

        // 1. 检查是否为广播地址
        if (frame.destAddr == BROADCAST_ADDR) {
            cout << "转发决策: 广播帧，向所有其他端口转发" << endl;
            printForwardingAction(frame.srcPort, true);
        }
        else {
            // 2. 查找目的地址
            auto it = macTable.find(frame.destAddr);
            if (it != macTable.end()) {
                destPort = it->second;
                // 目的地址已知
                if (destPort == frame.srcPort) {
                    cout << "转发决策: 目的端口(" << destPort
                        << ")与源端口相同，丢弃帧(过滤)" << endl;
                }
                else {
                    cout << "转发决策: 目的地址已知，转发到端口 " << destPort << endl;
                    printForwardingAction(frame.srcPort, false, destPort);
                }
            }
            else {
                // 3. 目的地址未知
                cout << "转发决策: 目的地址未知，泛洪(Flooding)" << endl;
                printForwardingAction(frame.srcPort, true);
            }
        }
    }

    // 打印具体的转发行为
    void printForwardingAction(int srcPort, bool isBroadcast, int specificPort = -1) {
        cout << "输出端口: ";
        if (isBroadcast) {
            // 泛洪到除源端口外的所有端口（假设只有端口1和2）
            if (srcPort != 1) cout << "1 ";
            if (srcPort != 2) cout << "2 ";
        }
        else {
            cout << specificPort;
        }
        cout << endl;
    }

    // 打印最终的MAC地址表
    void printMacTable() {
        cout << "================================" << endl;
        cout << "最终网桥 MAC 地址表:" << endl;
        cout << "地址\t端口" << endl;
        for (const auto& entry : macTable) {
            cout << entry.first << "\t" << entry.second << endl;
        }
        cout << "================================" << endl;
    }
};

int main() {
    Bridge bridge;
    vector<Frame> frames;
    int n;

    cout << "请输入帧的数量: ";
    if (!(cin >> n)) return 0;

    cout << "请输入帧信息 (格式: 源地址 源端口 目的地址)，例如: A 1 B" << endl;
    for (int i = 0; i < n; ++i) {
        Frame f;
        cin >> f.srcAddr >> f.srcPort >> f.destAddr;
        // 简单处理输入大小写
        if (f.srcAddr.length() > 0) f.srcAddr[0] = toupper(f.srcAddr[0]);
        if (f.destAddr.length() > 0) f.destAddr[0] = toupper(f.destAddr[0]);

        frames.push_back(f);
    }

    // 模拟处理过程
    for (const auto& frame : frames) {
        bridge.processFrame(frame);
    }

    // 输出最终结果
    bridge.printMacTable();

    return 0;
}