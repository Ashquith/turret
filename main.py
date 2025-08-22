# this program simulates a turret shooting an evading ship from a distance where time delay is significant


import pygame
import random


# CONSTANTS
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200

GRID_SIZE = 100 # in pixels

SHIP_RADIUS = 20 # in pixels, which also = meters
ACCELERATION = 100 # in pixels per second2
ROTATION_SPEED = 45 # turn capability in degrees per second

PROJECTILE_RADIUS = 20
PROJECTILE_SPEED = 1 # fraction between 0-1 where 1 is lightspeed
SHOT_DELAY = 0.5 # seconds between shots
VOLLEY_SIZE = 4 # shots in volley
MAX_SCATTER_DISTANCE = 25 # max projectile deviation in pixels(metres) per light second of delay

TIME_DELAY = 1 # distance between ship and turret in light-seconds
TICKS_IN_A_SEC = 60
TIME_DELAY_IN_TICKS = TICKS_IN_A_SEC * TIME_DELAY
SHOT_DELAY_IN_TICKS = TICKS_IN_A_SEC * SHOT_DELAY



class Ship(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(100, 0)
        self.acceleration_vector = pygame.Vector2(ACCELERATION, 0)
        self.turn_direction = 0
        self.radius = SHIP_RADIUS
        self.next_course_change = 0
        self.pos_history = []
        self.velocity_history = []
        self.acceleration_history = []
        self.hit_history = []
    
    def should_i_turn(self, tick):
        if tick == self.next_course_change:
            self.next_course_change += TIME_DELAY_IN_TICKS
            return True
        return False
    
    def log(self):
        self.pos_history.append(self.position.copy())
        self.velocity_history.append(self.velocity.copy())
        self.acceleration_history.append(self.acceleration_vector.copy())         

    def change_course(self):
        self.turn_direction = random.choice([-1, 1]) 
            
    def move(self):
        dt = 1 / TICKS_IN_A_SEC
        rotation_amount = ROTATION_SPEED * self.turn_direction * dt
        self.acceleration_vector = self.acceleration_vector.rotate(rotation_amount)
        self.velocity += self.acceleration_vector * dt
        self.position += self.velocity * dt

    def collision_check(self, live_projectiles, tick):
        for proj in live_projectiles[:]:
            if proj.arrival == tick:
                if self.position.distance_to(proj.position) <= self.radius:
                    proj.status = "hit"
                    live_projectiles.remove(proj)

                    hit_record = {
                        "tick": tick,
                        "impact_pos": proj.position,
                        "offset": self.position.distance_to(proj.position)
                    }                    
                    self.hit_history.append(hit_record)
                else:
                    proj.status = "miss"
                    live_projectiles.remove(proj)

        

        



class Turret:
    def __init__(self):
        self.shot_delay = SHOT_DELAY
        self.volley = VOLLEY_SIZE
        self.next_shot_tick = TIME_DELAY_IN_TICKS

    def should_i_shoot(self, tick):
        if tick < TIME_DELAY_IN_TICKS:
            return False
        if tick >= self.next_shot_tick:
            return True
        return False
    
    def aim(self, tick, target_pos, target_velocity, target_acceleration):
        
        target_predicted_pos = target_pos + (target_velocity * (TIME_DELAY + TIME_DELAY / PROJECTILE_SPEED)) + 0.5 * target_acceleration * (TIME_DELAY + TIME_DELAY / PROJECTILE_SPEED) * (TIME_DELAY + TIME_DELAY / PROJECTILE_SPEED)

        target_error_x = (random.uniform(0, TIME_DELAY) + random.uniform(0, TIME_DELAY) - TIME_DELAY) * MAX_SCATTER_DISTANCE # accuracy depends on time delay because time delay = distance.
        target_error_y = (random.uniform(0, TIME_DELAY) + random.uniform(0, TIME_DELAY) - TIME_DELAY) * MAX_SCATTER_DISTANCE
        
        target_x = target_predicted_pos.x + target_error_x
        target_y = target_predicted_pos.y + target_error_y
        
        
        return target_x, target_y, tick + TIME_DELAY_IN_TICKS / PROJECTILE_SPEED


    def shoot(self, x, y, arrival):
                
        new_projectile = Projectile(x,y,arrival)
        return new_projectile

     




class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, arrival):
        super().__init__()
        self.position = pygame.Vector2(x, y)
        self.radius = PROJECTILE_RADIUS
        self.arrival = arrival
        self.status = "live" # turns into hit or miss at arrival time



# ----------------------------------------------------------



def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Turret vs Ship")
    clock = pygame.time.Clock()
    hud_font = pygame.font.Font(None, 24)

    ship = Ship(SCREEN_WIDTH /2, SCREEN_HEIGHT /2)
    turret = Turret()
    projectiles = []
    live_projectiles = []
    tick = 0


    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((0, 0, 0))


        # UPDATE
        
        ship.log()
        if ship.should_i_turn(tick):
            ship.change_course()
        
        
        if turret.should_i_shoot(tick):
            for i in range(0, VOLLEY_SIZE): 
                projectile_data = turret.aim(tick, ship.pos_history[-TIME_DELAY_IN_TICKS], ship.velocity_history[-TIME_DELAY_IN_TICKS], ship.acceleration_history[-TIME_DELAY_IN_TICKS])
                new_projectile = turret.shoot(*projectile_data)
                projectiles.append(new_projectile)
                live_projectiles.append(new_projectile)
            turret.next_shot_tick = tick + SHOT_DELAY_IN_TICKS 

        ship.move()    
        ship.collision_check(live_projectiles, tick)    
        
        
        # DRAWING
        
        screen_center = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        camera_offset = ship.position - screen_center


        start_x = camera_offset.x - (camera_offset.x % GRID_SIZE)

        for x in range(int(start_x), int(camera_offset.x + SCREEN_WIDTH), GRID_SIZE):

            line_start = pygame.Vector2(x, camera_offset.y)
            line_end = pygame.Vector2(x, camera_offset.y + SCREEN_HEIGHT)
            pygame.draw.line(screen, (50, 50, 50), line_start-camera_offset, line_end-camera_offset, width=1)
        
        start_y = camera_offset.y - (camera_offset.y % GRID_SIZE)

        for y in range(int(start_y), int(camera_offset.y + SCREEN_HEIGHT), GRID_SIZE):

            line_start = pygame.Vector2(camera_offset.x, y)
            line_end = pygame.Vector2(camera_offset.x + SCREEN_WIDTH, y)
            pygame.draw.line(screen, (50, 50, 50), line_start-camera_offset, line_end-camera_offset, width=1)

        ship_screen_pos = ship.position - camera_offset
        pygame.draw.circle(screen, (255, 255, 255), ship_screen_pos, ship.radius)

        pygame.draw.line(screen, (255, 255, 255), ship_screen_pos, ship_screen_pos + ship.acceleration_vector, width=5)

        for proj in projectiles:
            proj_screen_pos = proj.position - camera_offset
            if proj.status == "live":
                contraction = round(((proj.arrival - tick)/TIME_DELAY_IN_TICKS) * PROJECTILE_RADIUS)
                pygame.draw.circle(screen, (0, 255, 0), proj_screen_pos, max(1, contraction), width = 2)
            elif proj.status == "hit":
                pygame.draw.circle(screen, (255, 0, 0), proj_screen_pos, 5, width = 0)
            elif proj.status == "miss":
                pygame.draw.circle(screen, (0, 0, 255), proj_screen_pos, 5, width = 0)

        # HUD
        
        time_passed = tick/TICKS_IN_A_SEC
        time_text_surface = hud_font.render(f"Simulation time: {time_passed:.0f} s", True, (255, 255, 255))
        screen.blit(time_text_surface, (20, 20))

        speed = ship.velocity.length()
        speed_text_surface = hud_font.render(f"Speed: {speed:.0f} p/s", True, (255, 255, 255))
        screen.blit(speed_text_surface, (20, 50))

        shots = len(projectiles)
        shots_text_surface = hud_font.render(f"Shots made: {shots:.0f}", True, (255, 255, 255))
        screen.blit(shots_text_surface, (20, 80))

        shots_hit = len(ship.hit_history)
        if shots == 0:
            shot_percent = 0
        else:
            shot_percent = shots_hit/(shots) * 100
        shots_hit_text_surface = hud_font.render(f"Shots hit: {shots_hit:.0f} ({shot_percent:.1f}%)", True, (255, 255, 255))
        screen.blit(shots_hit_text_surface, (20, 110))

        pygame.display.update()
        clock.tick(TICKS_IN_A_SEC)
        tick += 1




if __name__ == "__main__":
    main()