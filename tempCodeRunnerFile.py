dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        angle = math.degrees(math.atan2(dy, dx))  # Notice dy and dx, no negation

        rotated_image = pygame.transform.rotate(self.original_image, -angle)  # Negate angle here
        old_center = self.rect.center
        self.image = rotated_image
        self.rect = self.image.get_rect(center=old_center)