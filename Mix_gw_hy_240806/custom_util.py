from util import *
import math
import itertools
from itertools import permutations, combinations

# 2024-08-03 : all_partitions, find_nearest_bundles, custom_try_merging_multiple_bundles_by_distance, simulated_annealing 함수 추가
# 2024-08-06 : find_nearest_triples, get_infeasible_pairs 함수 추가

def get_infeasible_pairs(all_orders, dist_mat, all_riders):
    infeasible_pairs = set()
    num_orders = len(all_orders)

    for i in range(num_orders):
        for j in range(i + 1, num_orders):
            if i != j:
                order_i = all_orders[i]
                order_j = all_orders[j]
                feasible = False  # Assume infeasible until proven otherwise

                for rider in all_riders:
                    if get_total_volume(all_orders, [i, j]) <= rider.capa:
                        for shop_seq in itertools.permutations([i, j]):
                            for dlv_seq in itertools.permutations([i, j]):
                                feasibility = test_route_feasibility(all_orders, rider, shop_seq, dlv_seq)
                                if feasibility == 0:
                                    feasible = True  # Found a feasible combination
                                    break
                            if feasible:
                                break
                    if feasible:
                        break

                if not feasible:
                    infeasible_pairs.add((i, j))
                    infeasible_pairs.add((j, i))

    return infeasible_pairs

def find_nearest_triples(dist_mat, all_bundles):
    bundle_triples = []
    for i in range(len(all_bundles)):
        for j in range(i + 1, len(all_bundles)):
            for k in range(j + 1, len(all_bundles)):
                if i!=j and j!=k and i!= k :
                    bundle1 = all_bundles[i]
                    bundle2 = all_bundles[j]
                    bundle3 = all_bundles[k]
                    min_dist = min(
                        dist_mat[bundle1.shop_seq[-1]][bundle2.shop_seq[0]],
                        dist_mat[bundle2.shop_seq[-1]][bundle3.shop_seq[0]],
                        dist_mat[bundle3.shop_seq[-1]][bundle1.shop_seq[0]]
                    )
                    bundle_triples.append((min_dist, bundle1, bundle2, bundle3))
    bundle_triples = sorted(bundle_triples, key=lambda x: x[0])
    return bundle_triples

def find_nearest_triples_with_middle(all_orders, all_bundles):
    bundle_triples = []
    
    all_bundles_avg_loc = avg_loc(all_orders, all_bundles)
    all_bundles_dist_mat = dist_mat_by_loc(all_bundles_avg_loc)
    N = len(all_bundles)
    
    for i in range(len(all_bundles)):
        for j in range(i + 1, len(all_bundles)):
            for k in range(j + 1, len(all_bundles)):
                if i!=j and j!=k and i!= k :
                    dist_ij = all_bundles_dist_mat[i, j] + all_bundles_dist_mat[i+N, j+N] + (all_bundles_dist_mat[i, i+N] + all_bundles_dist_mat[i, j+N] + all_bundles_dist_mat[i+N, j] + all_bundles_dist_mat[j, j+N])*0.25
                    dist_jk = all_bundles_dist_mat[j, k] + all_bundles_dist_mat[j+N, k+N] + (all_bundles_dist_mat[j, j+N] + all_bundles_dist_mat[j, k+N] + all_bundles_dist_mat[j+N, k] + all_bundles_dist_mat[k, k+N])*0.25
                    dist_ki = all_bundles_dist_mat[k, i] + all_bundles_dist_mat[k+N, i+N] + (all_bundles_dist_mat[k, k+N] + all_bundles_dist_mat[k, i+N] + all_bundles_dist_mat[k+N, i] + all_bundles_dist_mat[i, i+N])*0.25
                    total_dist = dist_ij + dist_jk + dist_ki
                    
                    bundle1 = all_bundles[i]
                    bundle2 = all_bundles[j]
                    bundle3 = all_bundles[k]
                    
                    bundle_triples.append((total_dist, bundle1, bundle2, bundle3))
    bundle_triples = sorted(bundle_triples, key=lambda x: x[0])
    return bundle_triples

def draw_route_bundles(all_orders, all_bundles):
    plt.subplots(figsize=(12, 12))
    node_size = 5

    shop_x = [order.shop_lon for order in all_orders]
    shop_y = [order.shop_lat for order in all_orders]
    plt.scatter(shop_x, shop_y, c='red', s=node_size, label='SHOPS')

    dlv_x = [order.dlv_lon for order in all_orders]
    dlv_y = [order.dlv_lat for order in all_orders]
    plt.scatter(dlv_x, dlv_y, c='blue', s=node_size, label='DLVS')

    rider_idx = {
        'BIKE': 0,
        'CAR': 0,
        'WALK': 0
    }

    for bundle in all_bundles:
        rider_type = bundle.rider.type
        shop_seq = bundle.shop_seq
        dlv_seq = bundle.dlv_seq

        rider_idx[rider_type] += 1

        route_color = 'gray'
        if rider_type == 'BIKE':
            route_color = 'green'
        elif rider_type == 'WALK':
            route_color = 'orange'

        route_x = []
        route_y = []
        for i in shop_seq:
            route_x.append(all_orders[i].shop_lon)
            route_y.append(all_orders[i].shop_lat)

        for i in dlv_seq:
            route_x.append(all_orders[i].dlv_lon)
            route_y.append(all_orders[i].dlv_lat)

        plt.plot(route_x, route_y, c=route_color, linewidth=0.5)

    plt.legend()
    plt.show()

def count_bundles(all_bundles):
    counts = {
    'WALK': {'total': 0, 'lengths': {}},
    'BIKE': {'total': 0, 'lengths': {}},
    'CAR': {'total': 0, 'lengths': {}}
    }

    # 각 요소를 순회하며 카운팅
    for bundle in all_bundles:
        transport_type = bundle.rider.type
        counts[transport_type]['total'] += 1
    
        length = len(bundle.shop_seq)  # `shop_seq`의 길이를 기준으로 한다.
        if length not in counts[transport_type]['lengths']:
            counts[transport_type]['lengths'][length] = 0
        counts[transport_type]['lengths'][length] += 1

    # 결과 출력
    for transport_type, data in counts.items():
        total_count = data['total']
        print(f"{transport_type}: 총 {total_count}개")
        for length, count in sorted(data['lengths'].items()):
            print(f"  길이 {length}: {count}개")

def find_nearest_bundles(dist_mat, all_bundles):
    nearest_pairs = []
    for i, bundle1 in enumerate(all_bundles):
        min_dist = float('inf')
        nearest_bundle = None
        for j, bundle2 in enumerate(all_bundles):
            if i != j:
                dist = dist_mat[bundle1.shop_seq[-1], bundle2.shop_seq[0]] #단순하게 bundle1의 pickup 지점의 끝과, bundle2의 pickup 지점의 시작 사이의 거리를
                if dist < min_dist:
                    min_dist = dist
                    nearest_bundle = bundle2
        if nearest_bundle:
            nearest_pairs.append((min_dist, bundle1, nearest_bundle))
    nearest_pairs = sorted(nearest_pairs, key=lambda x: x[0])
    #print(f'Nearest pairs: {nearest_pairs}')  # 디버깅 출력
    return nearest_pairs

def all_partitions(orders):
    if len(orders) == 1:
        yield [orders]
        return

    first = orders[0]
    for smaller in all_partitions(orders[1:]):
        # insert `first` in each of the subpartition's subsets
        for n, subset in enumerate(smaller):
            yield smaller[:n] + [[first] + subset] + smaller[n + 1:]
        # put `first` in its own subset
        yield [[first]] + smaller

def filter_partitions(orders, num_parts):
    partitions = list(all_partitions(orders))
    return [p for p in partitions if len(p) == num_parts]

def evaluate_bundles(bundles):
    total_cost = sum(bundle.cost for bundle in bundles)
    return total_cost

def custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, bundles, all_riders, infeasible_pairs):
    merged_orders = list(set([order for bundle in bundles for order in bundle.shop_seq]))  # 중복 주문 제거
    total_volume = get_total_volume(all_orders, merged_orders)
    best_bundles = []
    min_total_cost = float('inf')

    def evaluate_bundles(bundles):
        total_cost = sum(bundle.cost for bundle in bundles)
        return total_cost

    def heuristic_merge(orders, rider):
        # Heuristic approach to find a feasible sequence
        shop_seq = [orders[0]]
        dlv_seq = [orders[0]]
        remaining_orders = set(orders[1:])
        while remaining_orders:
            last_shop = shop_seq[-1]
            nearest_order = min(remaining_orders, key=lambda x: dist_mat[last_shop][x])
            shop_seq.append(nearest_order)
            dlv_seq.append(nearest_order)
            remaining_orders.remove(nearest_order)
        return shop_seq, dlv_seq

    # Try to merge all orders into one bundle
    if len(merged_orders) <= 5:
        for rider in all_riders:
            if rider.available_number > 0 and total_volume <= rider.capa:
                for shop_pem in itertools.permutations(merged_orders):
                    if any((shop_pem[i], shop_pem[j]) in infeasible_pairs for i in range(len(shop_pem)) for j in range(i + 1, len(shop_pem))):
                        continue
                    for dlv_pem in itertools.permutations(merged_orders):
                        feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                        if feasibility_check == 0:
                            total_dist = get_total_distance(K, dist_mat, shop_pem, dlv_pem)
                            temp_bundle = Bundle(all_orders, rider, list(shop_pem), list(dlv_pem), total_volume, total_dist)
                            temp_bundle.update_cost()
                            current_cost = evaluate_bundles([temp_bundle])
                            if current_cost < min_total_cost:
                                min_total_cost = current_cost
                                best_bundles = [temp_bundle]
                                #print(f'one bundle : {best_bundles}')

    # Try to split into two bundles
    if len(merged_orders) > 1:
        two_partitions = filter_partitions(merged_orders, 2)
        for partition in two_partitions:
            if any((i, j) in infeasible_pairs for part in partition for i in part for j in part if i != j):
                continue
            candidate_bundles = []
            valid_partition = True
            for part in partition:
                part_volume = get_total_volume(all_orders, part)
                part_bundle = None
                for rider in all_riders:
                    if rider.available_number > 1 and part_volume <= rider.capa:
                        for shop_pem in itertools.permutations(part):
                            if any((shop_pem[i], shop_pem[j]) in infeasible_pairs for i in range(len(shop_pem)) for j in range(i + 1, len(shop_pem))):
                                continue
                            for dlv_pem in itertools.permutations(part):
                                feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                                if feasibility_check == 0:
                                    total_dist = get_total_distance(K, dist_mat, shop_pem, dlv_pem)
                                    part_bundle = Bundle(all_orders, rider, list(shop_pem), list(dlv_pem), part_volume, total_dist)
                                    part_bundle.update_cost()
                                    candidate_bundles.append(part_bundle)
                                    break
                            if part_bundle:
                                break
                    if part_bundle:
                        break
                if not part_bundle:
                    valid_partition = False
                    break

            if valid_partition and len(candidate_bundles) == 2:
                current_cost = evaluate_bundles(candidate_bundles)
                if current_cost < min_total_cost:
                    min_total_cost = current_cost
                    best_bundles = candidate_bundles
                    #print(f'two bundles : {best_bundles}')

    # Try to split into three bundles
    if len(merged_orders) > 2:
        three_partitions = filter_partitions(merged_orders, 3)
        for partition in three_partitions:
            if any((i, j) in infeasible_pairs for part in partition for i in part for j in part if i != j):
                continue
            candidate_bundles = []
            valid_partition = True
            for part in partition:
                part_volume = get_total_volume(all_orders, part)
                part_bundle = None
                for rider in all_riders:
                    if rider.available_number > 2 and part_volume <= rider.capa:
                        for shop_pem in itertools.permutations(part):
                            if any((shop_pem[i], shop_pem[j]) in infeasible_pairs for i in range(len(shop_pem)) for j in range(i + 1, len(shop_pem))):
                                continue
                            for dlv_pem in itertools.permutations(part):
                                feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                                if feasibility_check == 0:
                                    total_dist = get_total_distance(K, dist_mat, shop_pem, dlv_pem)
                                    part_bundle = Bundle(all_orders, rider, list(shop_pem), list(dlv_pem), part_volume, total_dist)
                                    part_bundle.update_cost()
                                    candidate_bundles.append(part_bundle)
                                    break
                            if part_bundle:
                                break
                    if part_bundle:
                        break
                if not part_bundle:
                    valid_partition = False
                    break

            if valid_partition and len(candidate_bundles) == 3:
                current_cost = evaluate_bundles(candidate_bundles)
                if current_cost < min_total_cost:
                    min_total_cost = current_cost
                    best_bundles = candidate_bundles
                    #print(f'three bundles : {best_bundles}')

    return best_bundles

# Simulated Annealing을 사용하여 번들을 최적화하는 함수
def simulated_annealing(all_bundles, K, dist_mat, all_orders, all_riders, timelimit=60, initial_temp=100, cooling_rate=0.99):
    current_solution = all_bundles  # 현재 해를 초기 해로 설정
    current_cost = sum(bundle.cost for bundle in all_bundles) / K  # 초기 해의 비용 계산
    best_solution = current_solution[:]  # 초기 해를 최적 해로 설정
    best_cost = current_cost  # 초기 해의 비용을 최적 비용으로 설정
    temperature = initial_temp  # 초기 온도 설정

    if len(current_solution) > 1:  # 번들이 2개 이상일 때만 수행
        i, j = random.sample(range(len(current_solution)), 2)  # 무작위로 두 번들을 선택
        selected_bundles = [current_solution[i], current_solution[j]]
        new_bundles = custom_try_merging_multiple_bundles_by_distance(K, dist_mat, all_orders, selected_bundles, all_riders)

        if new_bundles:  # 새로운 번들이 생성되었을 때
            new_cost = sum(bundle.cost for bundle in new_bundles) / K

            # 새로운 비용이 현재 비용보다 적거나, 확률적으로 수락할 때
            if new_cost < current_cost or random.uniform(0, 1) < math.exp((current_cost - new_cost) / temperature):
                current_solution = [bundle for k, bundle in enumerate(current_solution) if k != i and k != j] + new_bundles
                current_cost = new_cost

                if current_cost < best_cost:  # 새로운 해가 최적 해보다 나을 때
                    best_solution = current_solution[:]
                    best_cost = current_cost

    temperature *= cooling_rate  # 온도 감소

    return best_solution, best_cost  # 최적 해와 최적 비용 반환

def custom_try_bundle_rider_changing(all_orders, dist_mat, bundle, all_riders):
    old_rider = bundle.rider
    best_shop_seq = None
    best_dlv_seq = None
    best_rider = None
    min_total_cost = float('inf')
    
    for rider in all_riders:
        if bundle.total_volume <= rider.capa:
            orders = bundle.shop_seq
            
            for shop_pem in permutations(orders):
                for dlv_pem in permutations(orders):
                    feasibility_check = test_route_feasibility(all_orders, rider, shop_pem, dlv_pem)
                    if feasibility_check == 0:  # feasible!
                        total_dist = get_total_distance(len(all_orders), dist_mat, shop_pem, dlv_pem)
                        bundle.shop_seq = list(shop_pem)
                        bundle.dlv_seq = list(dlv_pem)
                        bundle.rider = rider
                        bundle.total_dist = total_dist
                        bundle.update_cost()
                        if bundle.cost < min_total_cost:
                            min_total_cost = bundle.cost
                            best_shop_seq = list(shop_pem)
                            best_dlv_seq = list(dlv_pem)
                            best_rider = rider

    if best_shop_seq and best_dlv_seq and best_rider:
        # Note: in-place replacing!
        bundle.shop_seq = best_shop_seq
        bundle.dlv_seq = best_dlv_seq
        bundle.rider = best_rider
        bundle.total_dist = get_total_distance(len(all_orders), dist_mat, best_shop_seq, best_dlv_seq)
        bundle.update_cost()  # update the cost with the best sequences and rider
        if old_rider != best_rider :
            old_rider.available_number += 1
            best_rider.available_number -= 1
        return True

    return False

def avg_loc(all_orders, all_bundles):
    bundles_index = [bundle.shop_seq for bundle in all_bundles]
    bundles_avg_loc = []
    for index_seq in bundles_index:
        ords_loc = [((order.shop_lat, order.shop_lon), (order.dlv_lat, order.dlv_lon)) for order in all_orders if order.id in index_seq]
        bundle_loc = np.zeros((2,2))
        for shop_loc, dlv_loc in ords_loc:
            bundle_loc[0] += np.array(shop_loc)
            bundle_loc[1] += np.array(dlv_loc)
        bundle_loc /= len(ords_loc)     
        bundles_avg_loc.append(bundle_loc)

    return bundles_avg_loc

def haversine_distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0  # 지구의 반지름 (킬로미터)
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance
    
def dist_mat_by_loc(all_bundles_avg_loc):
    
    N = len(all_bundles_avg_loc)
    bundles_dist_mat = np.zeros((2 * N, 2 * N))

    for i in range(N):
        for j in range(N):
            # 픽업 지점 간 거리
            bundles_dist_mat[i][j] = haversine_distance(all_bundles_avg_loc[i][0], all_bundles_avg_loc[j][0])
        
            # 배송 지점과 픽업 지점 간 거리
            bundles_dist_mat[i + N][j] = haversine_distance(all_bundles_avg_loc[i][1], all_bundles_avg_loc[j][0])
        
            # 픽업 지점과 배송 지점 간 거리
            bundles_dist_mat[i][j + N] = haversine_distance(all_bundles_avg_loc[i][0], all_bundles_avg_loc[j][1])
        
            # 배송 지점 간 거리
            bundles_dist_mat[i + N][j + N] = haversine_distance(all_bundles_avg_loc[i][1], all_bundles_avg_loc[j][1])
    
    return bundles_dist_mat