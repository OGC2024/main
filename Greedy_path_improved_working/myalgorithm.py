import heapq
from util import *
from custom_util import *

def algorithm(K, all_orders, all_riders, dist_mat, timelimit=60):

    start_time = time.time()

    for r in all_riders:
        r.T = np.round(dist_mat / r.speed + r.service_time)

    # A solution is a list of bundles
    solution = []

    #------------- Custom algorithm code starts from here --------------#

    walk_rider = None
    for r in all_riders:
        if r.type == 'WALK':
            walk_rider = r
        
    car_rider = None
    for r in all_riders:
        if r.type == 'CAR':
            car_rider = r

    all_bundles = []
    all_orders_tmp = all_orders.copy()
    infeasible_pairs = get_infeasible_pairs(all_orders, dist_mat, all_riders)
    print(f'num of infeasible pairs : {len(infeasible_pairs)}')
    heap = []
    cant_walk_list = []
    filt_ord = []
    
    for rider in all_riders:
        if rider.type == "WALK":
            walk_speed = rider.speed #도보 속도
            walk_time_mat = np.round(dist_mat/rider.speed + rider.service_time) #도보 이동시간
            break  

    for order in all_orders_tmp:
        ready_time = order.order_time + order.cook_time 
        time_diff = order.deadline - ready_time #해당 order의 준비~데드라인의 시간 차이
        walk_time = walk_time_mat[order.id][order.id+K] #해당 order를 배송하기 위해 도보로 이동할 떄 필요한 시간
    
        if time_diff < walk_time: #만약 주어진 시간이 모자라면
            cant_walk_list.append(order.id) #배달 불가능한 배달 번호 추가

    fcut_orders = [order for order in all_orders_tmp if order.id not in cant_walk_list] #불가능한 orders를 첫번째 잘라내고 남은 orders

    for f_order in fcut_orders:
        cant_merge_list = [f_order.id]
        for s_order in fcut_orders:
            #첫번째 order의 데드라인보다 두번째 order의 레디가 더 늦은 경우 cut
            if f_order.deadline < s_order.order_time + s_order.cook_time or f_order.order_time + f_order.cook_time > s_order.deadline:
                cant_merge_list.append(s_order.id)
            # 두번째 order의 레디에 2픽업->1도착의 이동 시간을 더해서 첫번째 order의 데드라인보다 늦으면 cut
            elif s_order.order_time + s_order.cook_time + walk_time_mat[s_order.id][f_order.id+K] > f_order.deadline:
                cant_merge_list.append(s_order.id)
        #print(f"{f_order.id}번째 order는 {cant_merge_list}와 결합 불가능")
        scut_orders = [order for order in fcut_orders if order.id not in cant_merge_list] #불가능한 orders를 두번째 잘라내고 남은 orders

        #Cut 이후에 merging 작업 진행
        ord = f_order
        new_bundle = Bundle(all_orders, walk_rider, [ord.id], [ord.id], ord.volume, dist_mat[ord.id, ord.id + K])
    
        for s_ord in scut_orders:
            new_bundle.shop_seq.append(s_ord.id)
            new_bundle.dlv_seq.append(s_ord.id)

            for dlv_pem in permutations(new_bundle.dlv_seq):
                feasibility_check = test_route_feasibility(all_orders, walk_rider, new_bundle.shop_seq, dlv_pem)
                if feasibility_check == 0: # feasible!
                    cost_1 = walk_rider.calculate_cost(dist_mat[ord.id, ord.id + K])
                    cost_2 = walk_rider.calculate_cost(dist_mat[s_ord.id, s_ord.id + K])
                    fea_bundle = Bundle(all_orders, walk_rider, new_bundle.shop_seq[:], list(dlv_pem),
                                        new_bundle.total_volume + s_ord.volume, get_total_distance(K, dist_mat, new_bundle.shop_seq, dlv_pem))
                    fea_bundle.update_cost()
                    cost_new = fea_bundle.cost
                    cost_diff = cost_1 + cost_2 - cost_new 
                    heapq.heappush(heap, [-cost_diff, fea_bundle.shop_seq, fea_bundle.dlv_seq, fea_bundle.total_volume, fea_bundle.total_dist])
                
            new_bundle.shop_seq.pop()
            new_bundle.dlv_seq.pop()
    
    while heap:
        smallest = heapq.heappop(heap)
        if all(item not in filt_ord for item in smallest[1]):
            filt_ord.extend(smallest[1])
            good_bundle = Bundle(all_orders, walk_rider, smallest[1], smallest[2], smallest[3], smallest[4])
            all_bundles.append(good_bundle)
            walk_rider.available_number -= 1

    # Update all_orders_tmp
    all_orders_tmp = [order for order in all_orders_tmp if order.id not in filt_ord]
    time_1 = time.time()
    draw_route_bundles(all_orders, all_bundles)
    # Create initial bundles using a greedy approach based on distance
    while all_orders_tmp:
        ord = all_orders_tmp.pop(0)
        # 일단 car_rider를 넣어 feasible한 bundle을 찾음
        new_bundle = Bundle(all_orders, car_rider, [ord.id], [ord.id], ord.volume, dist_mat[ord.id, ord.id + K])
        # Try to add the nearest orders to the current bundle
        while True:
            nearest_order = None
            min_dist = float('inf')
            for other_ord in all_orders_tmp:
                dist = dist_mat[ord.id, other_ord.id] + dist_mat[ord.id + K, other_ord.id + K] + (dist_mat[ord.id, ord.id + K] + dist_mat[ord.id, other_ord.id + K] + dist_mat[ord.id + K, other_ord.id] + dist_mat[other_ord.id, other_ord.id + K])*0.25
                if dist < min_dist and new_bundle.total_volume + other_ord.volume <= car_rider.capa:
                    min_dist = dist
                    nearest_order = other_ord

            if nearest_order:
                new_bundle.shop_seq.append(nearest_order.id)
                new_bundle.dlv_seq.append(nearest_order.id)
                new_bundle.total_volume += nearest_order.volume
                new_bundle.total_dist += min_dist

                feasibility_check = test_route_feasibility(all_orders, car_rider, new_bundle.shop_seq, new_bundle.dlv_seq)
                if feasibility_check == 0:  # Feasible
                    car_rider.available_number -= 1
                    all_orders_tmp.remove(nearest_order)
                    new_bundle.update_cost()
                    custom_try_bundle_rider_changing(all_orders, dist_mat, new_bundle, all_riders)
                else:
                    # Remove last added order if not feasible
                    new_bundle.shop_seq.pop()
                    new_bundle.dlv_seq.pop()
                    new_bundle.total_volume -= nearest_order.volume
                    new_bundle.total_dist -= min_dist
                    break

            else:
                break

        all_bundles.append(new_bundle)
    best_obj = sum((bundle.cost for bundle in all_bundles)) / K
    print(f'Initial best obj = {best_obj}')
    print(all_bundles)
    count_bundles(all_bundles)
    draw_route_bundles(all_orders, all_bundles)
    time_2 = time.time()
    print(f'Elapsed time for initializing: {time_2 - time_1}')

    '''
    1개짜리 처리 코드 넣기
    '''

    #1개짜리인 bundle을 모아서 따로 리스트에 저장
    #각 bundle 별로 merge
    cant_merge_list = []
    while True :
        single_order_bundles = [(-bundle.cost, bundle) for bundle in all_bundles if len(bundle.shop_seq) == 1 and bundle.shop_seq[0] not in cant_merge_list]
        if not single_order_bundles :
            break
        heapq.heapify(single_order_bundles)
        best_improvement = 0
        best_candidate = None
        best_new_bundles = None
        _, single_bundle = heapq.heappop(single_order_bundles)
        #print(f'single_bundle : {single_bundle}')
        Flag = False
        for i in range(len(all_bundles)):
            if all_bundles[i] != single_bundle :
                candidate_bundles = [single_bundle, all_bundles[i]]
                #print(f'candidate_bundles : {candidate_bundles}')
                new_bundles = custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, candidate_bundles, all_riders, infeasible_pairs)
                #print(f'new bundles : {new_bundles}')
                if new_bundles:
                    #print(new_bundles)
                    current_cost = sum(bundle.cost for bundle in candidate_bundles)
                    new_cost = sum(bundle.cost for bundle in new_bundles)
                    improvement = current_cost - new_cost
                    #print(f'improvement : {improvement}')
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_candidate = candidate_bundles
                        best_new_bundles = new_bundles
                        Flag = True
        if not Flag :
            cant_merge_list.append(single_bundle.shop_seq[0])

        if best_new_bundles:
            #print(f'best_new_bundles : {best_new_bundles}')
            #print(f'improvement : {best_improvement}')
            for tmp_bundle in best_candidate :
                #print(tmp_bundle)
                tmp_bundle.rider.available_number += 1
                all_bundles.remove(tmp_bundle)
            for tmp_bundle in best_new_bundles :
                tmp_bundle.rider.available_number -= 1
            all_bundles.extend(best_new_bundles)
            #count_bundles(all_bundles)
            
    print(f'single order bundle')
    count_bundles(all_bundles)
    #draw_route_bundles(all_orders, all_bundles)
    print(all_bundles)
    '''
        2개짜리 처리 코드 넣기
    '''

    # 길이가 2인 "CAR" 타입의 bundle을 모아서 따로 리스트에 저장
    # 각 bundle 별로 merge
    '''cant_merge_list = []
    while True:
        car_two_order_bundles = [(-bundle.cost, bundle) for bundle in all_bundles if len(bundle.shop_seq) == 2 and bundle.rider.type == "CAR" and all(order not in cant_merge_list for order in bundle.shop_seq)]
        if not car_two_order_bundles:
            break
        heapq.heapify(car_two_order_bundles)
        best_improvement = 0
        best_candidate = None
        best_new_bundles = None
        _, two_order_bundle = heapq.heappop(car_two_order_bundles)
        #print(f'two_order_bundle : {two_order_bundle}')
        Flag = False
        for i in range(len(all_bundles)):
            if all_bundles[i] != two_order_bundle:
                candidate_bundles = [two_order_bundle, all_bundles[i]]
                #print(f'candidate_bundles : {candidate_bundles}')
                new_bundles = custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, candidate_bundles, all_riders, infeasible_pairs)
                #print(f'new bundles : {new_bundles}')
                if new_bundles:
                    #print(new_bundles)
                    current_cost = sum(bundle.cost for bundle in candidate_bundles)
                    new_cost = sum(bundle.cost for bundle in new_bundles)
                    improvement = current_cost - new_cost
                    #print(f'improvement : {improvement}')
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_candidate = candidate_bundles
                        best_new_bundles = new_bundles
                        Flag = True
        if not Flag:
            cant_merge_list.extend(two_order_bundle.shop_seq)

        if best_new_bundles:
            #print(f'best_new_bundles : {best_new_bundles}')
            #print(f'improvement : {best_improvement}')
            for tmp_bundle in best_candidate:
                #print(tmp_bundle)
                tmp_bundle.rider.available_number += 1
                all_bundles.remove(tmp_bundle)
            for tmp_bundle in best_new_bundles:
                tmp_bundle.rider.available_number -= 1
            all_bundles.extend(best_new_bundles)
            #count_bundles(all_bundles)

    print(f'car two order bundle')
    count_bundles(all_bundles)
    #draw_route_bundles(all_orders, all_bundles)
    print(all_bundles)'''

    #---------------
    iter = 0
    while time.time() - start_time < timelimit and len(all_bundles) > 1:
        iter += 1
        nearest_triples = find_nearest_triples(dist_mat, all_bundles)
        improved = False
        for min_dist, bundle1, bundle2, bundle3 in nearest_triples:
            new_bundles = custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, [bundle1, bundle2, bundle3], all_riders, infeasible_pairs)
            if new_bundles:
                improvement = sum(bundle.cost for bundle in [bundle1, bundle2, bundle3]) - sum(bundle.cost for bundle in new_bundles)
                if improvement > 0:
                    bundle1.rider.available_number += 1
                    bundle2.rider.available_number += 1
                    bundle3.rider.available_number += 1
                    all_bundles.remove(bundle1)
                    all_bundles.remove(bundle2)
                    all_bundles.remove(bundle3)
                    for new_bundle in new_bundles:
                        new_bundle.rider.available_number -= 1
                        all_bundles.append(new_bundle)
                    cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
                    if cur_obj < best_obj:
                        best_obj = cur_obj
                        count_bundles(all_bundles)
                        draw_route_bundles(all_orders, all_bundles)
                    improved = True
                    break
            if time.time() - start_time >= timelimit:
                break
        if not improved:
            break
    '''iter = 0
    while time.time() - start_time < timelimit and len(all_bundles) > 1:
        iter += 1
        nearest_pairs = find_nearest_bundles(dist_mat, all_bundles)

        improved = False
        for min_dist, bundle1, bundle2 in nearest_pairs:
            #print(bundle1, bundle2)
            new_bundles = custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, [bundle1, bundle2], all_riders)
            #print(f'new_bundles : {new_bundles}')
            if new_bundles :
                improvement = sum(bundle.cost for bundle in [bundle1, bundle2]) - sum(bundle.cost for bundle in new_bundles)
                if improvement > 0:
                    #print(f'Improvement: {improvement}, New bundles: {new_bundles}')
                    bundle1.rider.available_number += 1
                    bundle2.rider.available_number += 1
                    all_bundles.remove(bundle1)
                    all_bundles.remove(bundle2)
                    for new_bundle in new_bundles:
                        new_bundle.rider.available_number -= 1
                        all_bundles.append(new_bundle)
                    cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
                    if cur_obj < best_obj:
                        best_obj = cur_obj
                        #print(f'Best obj = {best_obj}')
                        count_bundles(all_bundles)
                        draw_route_bundles(all_orders, all_bundles)
                    improved = True
                    break
            if time.time() - start_time >= timelimit :
                break
            if improved:
                break'''
    '''
    if not improved:  # If no improvement, switch to simulated annealing
        sa_timelimit = timelimit - (time.time() - start_time)
        if sa_timelimit > 0 :
            all_bundles, _ = simulated_annealing(all_bundles, K, dist_mat, all_orders, all_riders, sa_timelimit)
            cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
            if cur_obj < best_obj:
                best_obj = cur_obj
                print(f'Best obj (SA) = {best_obj}')
    '''

    cur_obj = sum((bundle.cost for bundle in all_bundles)) / K
    if cur_obj < best_obj:
        best_obj = cur_obj
        print(f'Final best obj = {best_obj}')
    count_bundles(all_bundles)
    solution = [
        [bundle.rider.type, bundle.shop_seq, bundle.dlv_seq]
        for bundle in all_bundles
    ]
    print(solution)

    return solution
