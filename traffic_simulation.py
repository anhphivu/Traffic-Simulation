def process(lst):
    '''
    This function take input of a list of string and convert it into a list 
    of tuple. For example ['(4, 1)' , '(1, 4)'] --> [(4, 1), (1, 4)] and remove
    the '\n'
    '''
    answer_lst = []
    for elem in lst:
        if '\n' in elem:
            elem = elem[:-1]
        elem = elem[1:-1]
        num_lst = elem.split(",")
        tup = []
        for char in num_lst:
            tup.append(int(char))
        answer_lst.append(tuple(tup))
    return list(answer_lst)


def load_road_network(filename):
    '''
    Take input as a file text and return two dictionary, one represent the 
    intersections where its key is the intersection's ID and the value is the 
    list of traffic signal, the other dictionary represent the roads where the 
    key is the tuple with source and destination and the value is the number of 
    timesteps.
    '''
    
    type = None
    current = None
    intersections = dict()
    roads = dict()

    with open(filename, 'r') as fp:
        for line in fp.readlines():
            if line == '\n':
                continue
                
            if line[0:14] == '#Intersection:':
                type = 'intersection'
                current = int(line[14:])
                intersections[current] = []

            if line == '#Roads\n':
                type = 'road'

            if type == 'intersection' and line[0:14] != '#Intersection:':
                tuple_list = line.split(";")
                intersections[current].append(tuple_list)

            if type == 'road' and line != '#Roads\n':
                tup_lst = line.split(":")
                if ('\n' in tup_lst[1]):
                    tup_lst[1] = tup_lst[1][:-1]
                tup_lst[0] = tup_lst[0][1:-1]
                num_lst = []
                
                for ele in tup_lst[0].split(','):
                    num_lst.append(int(ele))
                roads[tuple(num_lst)] = int(tup_lst[1])
                               
    answer_intersections = dict()
    for key in intersections:
        answer_intersections[key] = []
        for lst in intersections[key]:
            answer_intersections[key].append(process(lst))
                
    return answer_intersections, roads

def path_cost(path, intersections, road_times):
    '''
    This function takes the input path as a list of nodes and return the number
    of path it takes to get from the start to the end. Return None when we have 
    to stop at an intersection.
    '''
    path_count = 0
    for i in range(len(path) - 2):
        start = path[i] 
        mid = path[i + 1] 
        end = path[i + 2] 
        path_count += road_times[(start, mid)] 
        
        intersection = intersections[mid] 
        timestep = path_count % len(intersection) 
        if (start, end) not in intersection[timestep]: 
            return None
                                                
    path_count += road_times[(path[-2], path[-1])]

    return path_count  
        
def intersection_step(intersections, road_times, intersection_id, 
                      cars_at_intersection, timestep):
    '''
    This function return a list of cars that are allowed to proceed through
    a given intersection at a given current timestep
    '''
    lst_car = []
    lst_path = []
    for car in cars_at_intersection:
        car_path = car[1]
        start_index = car_path.index(intersection_id) - 1
        end_index = start_index + 2
        (start, end) = (car_path[start_index], car_path[end_index])
        intersection = intersections[intersection_id]
        current_timestep = timestep % len(intersection)
        if ((start, end) in intersection[current_timestep] 
        and (start, end) not in lst_path):
            lst_car.append(car[0])
            lst_path.append((start, end))       
    lst_car_sorted = sorted(lst_car)
    return lst_car_sorted

def made_new_cars(cars_to_add, road_times, timestep):
    '''
    This function add a new item(the current node) to the tuple in cars_to_add
    '''
    new_cars = []
    for car in cars_to_add:
        if car[2] == timestep:
            road_time = road_times[car[1][0], car[1][1]]
            arrival = timestep + road_time
            new_cars.append((car[0], car[1], arrival, car[1][1]))
    return new_cars

def check_loop(cars, timestep, cars_to_add):
    '''
    This function check if all the cars have reached its destination or not
    '''
    for car in cars_to_add:
        if car[2] >= timestep:
            return True
    for car in cars:
        if car[3] != car[1][-1] or car[2] >= timestep:
            return True
    return False

def check_intersection(cars, timestep, intersections):
    '''
    This function revert the new tuple into its original 
    state so it can be use in the function 'intersection_step'
    '''
    moving_cars = []
    for intersection in intersections:
        cars_at_intersection = []
        for car in cars:
            if car[3] == intersection and car[2] <= timestep:
                cars_at_intersection.append(car[:3])

        moving_cars += (intersection_step(intersections, [], intersection, 
                                          cars_at_intersection, timestep))
    return moving_cars

def id_to_car(cars_id, cars):
    '''
    This function is used to get the car_id from the list of cars
    '''
    cars_value = []
    for car_id in cars_id:
        for car in cars:
            if car[0] == car_id:
                cars_value.append(car)
    return cars_value

def check_action(car, timestep):
    '''
    This function check what each car is doing and return in action
    '''
    current_node = car[3]
    path = car[1]
    if car[2] > timestep:
        start = path[path.index(current_node) - 1]
        return f'drive({timestep}, {car[0]}, {start}, {current_node})'
    elif current_node  == path[-1]:
        return f'arrive({timestep}, {car[0]}, {current_node})'
    else:
        return f'wait({timestep}, {car[0]}, {current_node})'

def check_arrival(cars, timestep):
    '''
    This fucntion check whether if the car has arrived at its destination yet
    '''
    arrival_cars = []
    for car in cars:
        current_node = car[3]
        path = car[1]
        if current_node == path[-1] and car[2] <= timestep:
            arrival_cars.append(car)
    return arrival_cars

def simulate(intersections, road_times, cars_to_add):
    timestep = 0
    new_cars = []
    lst_actions = []
    while check_loop(new_cars, timestep, cars_to_add):
        moving_cars_id = []
        new_cars += made_new_cars(cars_to_add, road_times, timestep)
        moving_cars_id += check_intersection(new_cars, timestep, intersections)
        moving_cars = id_to_car(moving_cars_id, new_cars)
        for car in moving_cars:
            path = car[1]
            current_node = car[3]
            next_node = path[path.index(current_node) + 1]
            new_cars.remove(car)
            arrival = timestep + road_times[current_node, next_node]
            new_cars.append((car[0], car[1], arrival, next_node))
        new_cars.sort()
        for car in new_cars:
            lst_actions.append(check_action(car, timestep))
        for car in check_arrival(new_cars, timestep):
            new_cars.remove(car)
        timestep += 1
    return lst_actions
        