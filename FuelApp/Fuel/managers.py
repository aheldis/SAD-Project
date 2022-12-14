from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password, first_name, last_name, car_licence, phone_number, **extra_fields):
        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            car_licence=car_licence,
            phone_number=phone_number,
            **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(username, password, "_", "_", "_", "_", **extra_fields)
