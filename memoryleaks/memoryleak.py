"""
内存泄露测试
"""
# import time
#
# import objgraph
# import schedule


# class MLE(object):
#
#     def __init__(self):
#         pass
#
#     def dosomething(self):
#         objgraph.show_growth()
#
#         a = {}
#         for i in range(10000):
#             a[i] = i
#             time.sleep(0.1)
#
# if __name__ == '__main__':
#     mle = MLE()
#     schedule.every(1).minutes.do(mle.dosomething)
import time
import objgraph
import schedule
from pympler import tracker, muppy, summary

tr = tracker.SummaryTracker()


def dosomething():
    print("memory total")
    all_objects = muppy.get_objects()
    sum1 = summary.summarize(all_objects)
    summary.print_(sum1)

    print("memory difference")
    tr.print_diff()
    # ........ 爬取任务
    a = {}
    for i in range(10000):
        a[i] = i
        time.sleep(0.5)
    return


schedule.every(1).minutes.do(dosomething())