# this program simulates a turret shooting an evading ship from a distance where time delay is significant


import pygame
import random


# CONSTANTS
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200

GRID_SIZE = 200 # in pixels
MOUSEOVER_DELAY = 0.6 # in seconds

SHIP_RADIUS = 20 # in pixels, which also = meters
ACCELERATION = 50 # in pixels per second2
ROTATION_SPEED = 90 # turn capability in degrees per second
BOOST_MODIFIER = 4

PROJECTILE_RADIUS = 20
PROJECTILE_SPEED = 1 # fraction between 0-1 where 1 is lightspeed
PROJECTILE_DAMAGE = 5 # how much hp is lost on hit
SHOT_DELAY = 0.1 # seconds between shots
VOLLEY_SIZE = 1 # shots in volley
MAX_SCATTER_DISTANCE = 20 # max projectile deviation in pixels(metres) per light second of delay

TIME_DELAY = 1 # distance between ship and turret in light-seconds
TICKS_IN_A_SEC = 60
TIME_DELAY_IN_TICKS = TICKS_IN_A_SEC * TIME_DELAY
SHOT_DELAY_IN_TICKS = TICKS_IN_A_SEC * SHOT_DELAY


class Ship(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, -100)
        self.acceleration_vector = pygame.Vector2(0, -ACCELERATION)
        self.boost = 1
        self.hp = 100
        self.boost_fuel = 3000
        self.boost_til = 0
        self.turn_direction = 0
        self.rotation = 0
        self.radius = SHIP_RADIUS
        self.original_image = pygame.image.load("spaceship.png").convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (80, 80))
        self.original_image2 = pygame.image.load("spaceship2.png").convert_alpha()
        self.original_image2 = pygame.transform.scale(self.original_image2, (80, 80))
        self.image = self.original_image
        self.image2 = self.original_image2
        self.rect = self.image.get_rect(center=self.position)
        self.next_course_change = 0
        self.pos_history = []
        self.velocity_history = []
        self.acceleration_history = []
        self.hit_history = []
    
    def piloting(self, tick, autopilot):
        self.boost = 1

        if autopilot:
            if tick >= self.next_course_change:
                self.next_course_change += TIME_DELAY_IN_TICKS
                self.turn_direction = random.choice([-1, 1])
            if self.boost_til > tick:
                self.activate_boost()
            elif self.boost_fuel >= TIME_DELAY_IN_TICKS * 30:
                self.boost_til = random.uniform(10,90) + tick

        else:
            self.turn_direction = 0
            keys = pygame.key.get_pressed()
            if keys[pygame.K_d]:
                self.turn_direction = 1            
            if keys[pygame.K_a]:
                self.turn_direction = -1            
            if keys[pygame.K_SPACE]:
                self.activate_boost()

    def activate_boost (self):
        if self.boost_fuel >= 10:
            self.boost = BOOST_MODIFIER
            self.boost_fuel -= 10
    
    def log(self):
        self.pos_history.append(self.position.copy())
        self.velocity_history.append(self.velocity.copy())
        self.acceleration_history.append(self.acceleration_vector.copy())       
            
    def move(self):
        if self.boost == 1:
            self.boost_fuel +=5
            self.boost_fuel = min(self.boost_fuel, 3000)

        dt = 1 / TICKS_IN_A_SEC
        rotation_amount = ROTATION_SPEED * self.turn_direction * dt
        self.acceleration_vector = self.acceleration_vector.rotate(rotation_amount)
        self.velocity += self.acceleration_vector * dt * self.boost
        self.position += self.velocity * dt

        right_vector = pygame.Vector2(0, -1)
        self.rotation = right_vector.angle_to(self.acceleration_vector)
        if self.boost == 1:
            self.image = pygame.transform.rotate(self.original_image, -self.rotation)
            self.rect = self.image.get_rect(center=self.position)
        else:
            self.image = pygame.transform.rotate(self.original_image2, -self.rotation)
            self.rect = self.image.get_rect(center=self.position)              
        

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
                    self.hp -= PROJECTILE_DAMAGE
                else:
                    proj.status = "miss"
                    live_projectiles.remove(proj)

    def is_inside (self, mousepos):
        return self.position.distance_to(mousepos) <= self.radius
        



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
        self.explosion_radius = 0
        self.explosion_width = 0

    def explosion(self, time):

        self.explosion_radius = round(time * 2)
        self.explosion_width = max (1, round(12 - time/4))
   


# ----------------------------------------------------------

def wait_for_key(clock):    
    waiting = True
    while waiting:
        clock.tick(TICKS_IN_A_SEC)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "space"
                else:
                    return "quit"


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Turret vs Ship")
    clock = pygame.time.Clock()
    hud_font = pygame.font.Font(None, 24)
    end_font = pygame.font.Font(None, 64)
    autopilot = False

    ship = Ship(SCREEN_WIDTH /2, SCREEN_HEIGHT /2)
    turret = Turret()
    projectiles = []
    live_projectiles = []
    tick = 0
    game_over_time = 0
    

    started_hovering = False

    game_state = "starting"
    while game_state == "starting":
        screen.fill((0, 0, 0))
        game_text = end_font.render("Press spacebar for autopilot, any other key for manual", True, (255, 0, 0))
        text_rect = game_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        screen.blit(game_text, text_rect)
        pygame.display.update()

        key = wait_for_key(clock)        
        if key == "space":
            autopilot = True
        game_state = "playing"
    


    while game_state == "playing" or game_state == "ending":  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state = "game_over"
        screen.fill((0, 0, 0))
          

        if game_state == "playing":
            ship.log()
            ship.piloting(tick, autopilot)            
            
            if turret.should_i_shoot(tick):
                for i in range(0, VOLLEY_SIZE): 
                    projectile_data = turret.aim(tick, ship.pos_history[-TIME_DELAY_IN_TICKS], ship.velocity_history[-TIME_DELAY_IN_TICKS], ship.acceleration_history[-TIME_DELAY_IN_TICKS])
                    new_projectile = turret.shoot(*projectile_data)
                    projectiles.append(new_projectile)
                    live_projectiles.append(new_projectile)
                turret.next_shot_tick = tick + SHOT_DELAY_IN_TICKS 

            ship.move()    
            ship.collision_check(live_projectiles, tick) 

            if ship.hp <= 0:
                game_state = "ending"
                game_over_time = tick   
        
        
        # DRAWING
        
        screen_center = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        camera_offset = ship.position - screen_center

        # GRID

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

        # SHIP
        
        ship_screen_pos = ship.position - camera_offset
        ship.rect.center = ship_screen_pos
        
        if game_state == "playing":
            screen.blit(ship.image, ship.rect)
        if game_state == "ending":
            from_hit_time = tick - game_over_time

            explosion_radius = round(from_hit_time * 3)
            explosion_width = max (1, round(24 - from_hit_time/6))
                        
            red_level = max(0, 255 - from_hit_time * 2.0)
            secondary = max(0, round(explosion_radius * 0.9)-20)
            pygame.draw.circle(screen, (red_level, 0, 0), ship_screen_pos + (10,10), explosion_radius, width = explosion_width)
            pygame.draw.circle(screen, (red_level, 0, 0), ship_screen_pos + (-10,-10), explosion_radius, width = explosion_width)
            pygame.draw.circle(screen, (red_level, 0, 0), ship_screen_pos + (5,0), explosion_radius, width = explosion_width)
            pygame.draw.circle(screen, (max(0, red_level-50), 0, 0), ship_screen_pos + (5,0), secondary, width = max(1, explosion_width-2))
            pygame.draw.circle(screen, (max(0, red_level-50), 0, 0), ship_screen_pos + (5,5), secondary, width = max(1, explosion_width-2))
            pygame.draw.circle(screen, (max(0, red_level-50), 0, 0), ship_screen_pos + (-5,0), secondary, width = max(1, explosion_width-2))
            pygame.draw.circle(screen, (max(0, red_level-50), 0, 0), ship_screen_pos + (-5,5), secondary, width = max(1, explosion_width-2))
            pygame.draw.circle(screen, (max(0, red_level-50), 0, 0), ship_screen_pos, secondary, width = max(1, explosion_width-2))

         # PROJECTILES

        for proj in projectiles:
            proj_screen_pos = proj.position - camera_offset
            if proj.status == "live":
                contraction = round(((proj.arrival - tick)/TIME_DELAY_IN_TICKS) * PROJECTILE_RADIUS)
                pygame.draw.circle(screen, (0, 255, 0), proj_screen_pos, max(1, contraction), width = 2)
            elif proj.status == "hit":
                from_hit_time = tick - proj.arrival
                if from_hit_time < TICKS_IN_A_SEC * 2:
                    proj.explosion(from_hit_time)
                    red_level = max(0, 255 - from_hit_time * 2.5)
                    secondary = max(0, round(proj.explosion_radius * 0.9)-20)
                    pygame.draw.circle(screen, (red_level, 0, 0), proj_screen_pos, proj.explosion_radius, width = proj.explosion_width)
                    pygame.draw.circle(screen, (max(0, red_level-50), 0, 0), proj_screen_pos, secondary, width = max(1, proj.explosion_width-2))
                pygame.draw.circle(screen, (255, 0, 0), proj_screen_pos, 3, width = 0)
            elif proj.status == "miss":
                pygame.draw.circle(screen, (0, 0, 255), proj_screen_pos, 3, width = 0)

        # HUD
        
        time_passed = tick/TICKS_IN_A_SEC
        if game_state == "ending":
            time_passed = game_over_time/TICKS_IN_A_SEC
        time_text_surface = hud_font.render(f"Simulation time: {time_passed:.0f} s", True, (255, 255, 255))
        screen.blit(time_text_surface, (20, 20))



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

        # BARS

        bar_pos = ship.position - camera_offset + (-50, 60)

        bar_rect = pygame.Rect(bar_pos.x, bar_pos.y, max(0, ship.hp), 10)
        bar_border = pygame.Rect(bar_pos.x, bar_pos.y, 100, 10)
        pygame.draw.rect(screen, (155,0,0), bar_rect, width = 0)
        pygame.draw.rect(screen, (255,0,0), bar_border, width=1)

        boost_bar_rect = pygame.Rect(bar_pos.x, bar_pos.y+15, round(ship.boost_fuel/30), 10)
        boost_bar_border = pygame.Rect(bar_pos.x, bar_pos.y+15, 100, 10)
        pygame.draw.rect(screen, (0,130,255), boost_bar_rect, width = 0)
        pygame.draw.rect(screen, (100,130,255), boost_bar_border, width=1)

        # MOUSEOVER

        mouse_pos = pygame.mouse.get_pos() + camera_offset
        is_hovering = ship.is_inside(mouse_pos)

        
        tooltip_pos = ship.position - camera_offset + (60,-30)


        if is_hovering and not started_hovering:
            hover_start = tick
            started_hovering = True
        elif is_hovering and started_hovering:
            if tick - hover_start >= MOUSEOVER_DELAY * TICKS_IN_A_SEC:
                speed = ship.velocity.length()
                speed_text_surface = hud_font.render(f"Speed: {speed:.0f} p/s", True, (255, 255, 255))
                acceleration_text_surface = hud_font.render(f"Acceleration: {ACCELERATION * ship.boost:.0f} p/s2", True, (255, 255, 255))
                hp_text_surface = hud_font.render(f"HP: {ship.hp:.0f} / 100", True, (255, 255, 255))
                boost_text_surface = hud_font.render(f"Boost fuel: {ship.boost_fuel:.0f} / 3000", True, (255, 255, 255))

                tooltip_rect = pygame.Rect(tooltip_pos.x, tooltip_pos.y, 200, 100)
                overlay = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
                overlay.fill((50, 50, 50, 80))
                screen.blit(overlay, tooltip_rect.topleft)
                screen.blit(speed_text_surface, (tooltip_pos)+(10,10))
                screen.blit(acceleration_text_surface, (tooltip_pos)+(10,30))
                screen.blit(hp_text_surface, (tooltip_pos)+(10,50))
                screen.blit(boost_text_surface, (tooltip_pos)+(10,70))
        elif not is_hovering:
            started_hovering = False
            hover_start = 0

        # retry screen

        if game_state == "ending" and tick > game_over_time + 120:
            game_over_text = end_font.render("GAME OVER", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            screen.blit(game_over_text, text_rect)
            retry_text = hud_font.render("Press space to retry", True, (255, 0, 0))
            text_rect = retry_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30))
            screen.blit(retry_text, text_rect)
        if game_state == "ending" and tick > game_over_time + 125:
            
            quit_or_restart = wait_for_key(clock)
            if quit_or_restart == "quit":
                pygame.quit()
                return
            if quit_or_restart == "space":
                ship = Ship(SCREEN_WIDTH /2, SCREEN_HEIGHT /2)
                turret = Turret()
                projectiles = []
                live_projectiles = []
                tick = 0
                game_over_time = 0
                started_hovering = False
                game_state = "playing"


        pygame.display.update()
        clock.tick(TICKS_IN_A_SEC)
        tick += 1

    pygame.quit()


if __name__ == "__main__":
    main()