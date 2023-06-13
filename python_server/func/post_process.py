import numpy as np

#xyxy값 튜플 두개와 point값 튜플을 받아서 point가 xyxy안에 있는지 확인
def point_in_box(box_pt1 : tuple, box_pt2 : tuple, point : tuple) -> bool :
    return (box_pt1[0] <= point[0] and point[0] <= box_pt2[0] and box_pt1[1] <= point[1] and point[1] <= box_pt2[1])

#전체 컨테이너에서 현재 밀접하게 겹쳐있는 박스들의 index 튜플을 반환
def del_overlap(container):
    n=len(container)
    mid_container = []
    overlapped_index = []
    
    for box in container:
        mid_container.append((((box[0]+box[2])/2), (box[1] + box[3])/2))

    for i in range(n-1):
        for j in range(i+1,n):
            if point_in_box((container[i][0],container[i][1]),(container[i][2],container[i][3]), mid_container[j]):
                overlapped_index.append((i,j))
    
    cur = 0
    for i,j in overlapped_index:
        container = np.delete(container, i-cur, axis=0)
        cur+=1
    
    return container
