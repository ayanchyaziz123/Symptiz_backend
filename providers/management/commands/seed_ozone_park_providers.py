"""
Management command to seed providers in Ozone Park, NYC
Usage: python manage.py seed_ozone_park_providers
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from providers.models import Provider, Specialty, Clinic, ProviderClinicAffiliation, ProviderAvailability
from django.db import transaction
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds provider data for Ozone Park, NYC area'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to seed Ozone Park providers...'))

        try:
            with transaction.atomic():
                # Create/Get Specialties
                specialties = self.create_specialties()

                # Create Clinic in Ozone Park
                clinic = self.create_ozone_park_clinic()

                # Create Providers
                providers = self.create_providers(specialties, clinic)

                self.stdout.write(self.style.SUCCESS(
                    f'\n✅ Successfully created {len(providers)} providers in Ozone Park, NYC!'
                ))
                self.stdout.write(self.style.SUCCESS(f'✅ Created clinic: {clinic.name}'))

                # Display created providers
                self.stdout.write(self.style.WARNING('\n📋 Created Providers:'))
                for provider in providers:
                    self.stdout.write(f'  - Dr. {provider.user.get_full_name()} ({provider.specialties.first().name})')
                    self.stdout.write(f'    Email: {provider.user.email}')
                    self.stdout.write(f'    Password: password123')
                    self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise

    def create_specialties(self):
        """Create or get existing specialties"""
        self.stdout.write('Creating specialties...')

        specialty_data = [
            ('Family Medicine', '👨‍⚕️', 'General healthcare for all ages'),
            ('Internal Medicine', '🩺', 'Adult disease prevention and treatment'),
            ('Pediatrics', '👶', 'Healthcare for infants, children, and adolescents'),
            ('Cardiology', '❤️', 'Heart and cardiovascular system'),
            ('Dermatology', '🧴', 'Skin, hair, and nail conditions'),
        ]

        specialties = {}
        for name, icon, desc in specialty_data:
            specialty, created = Specialty.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'description': desc}
            )
            specialties[name] = specialty
            if created:
                self.stdout.write(f'  ✓ Created specialty: {name}')

        return specialties

    def create_ozone_park_clinic(self):
        """Create a clinic in Ozone Park, NYC"""
        self.stdout.write('Creating Ozone Park clinic...')

        clinic, created = Clinic.objects.get_or_create(
            name='Ozone Park Family Medical Center',
            defaults={
                'address': '101-02 Cross Bay Boulevard',
                'city': 'Ozone Park',
                'state': 'NY',
                'zip_code': '11417',
                'phone': '(718) 845-1234',
                'email': 'contact@ozoneparkmedical.com',
                'latitude': Decimal('40.6765'),
                'longitude': Decimal('-73.8442'),
                'clinic_type': 'family_practice',
                'accepts_medicaid': True,
                'accepts_medicare': True,
                'sliding_scale': True,
                'free_services': False,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created clinic: {clinic.name}'))
        else:
            self.stdout.write(f'  → Clinic already exists: {clinic.name}')

        return clinic

    def create_providers(self, specialties, clinic):
        """Create sample providers"""
        self.stdout.write('Creating providers...')

        providers_data = [
            {
                'username': 'dr_johnson_oz',
                'email': 'mjohnson@ozoneparkmed.com',
                'first_name': 'Michael',
                'last_name': 'Johnson',
                'specialty': 'Family Medicine',
                'license': 'NY-FM-123456',
                'experience': 15,
                'bio': 'Board-certified family physician with 15 years of experience serving the Ozone Park community. Specialized in preventive care and chronic disease management.',
                'education': 'MD from NYU School of Medicine',
                'languages': 'English, Spanish',
                'fee': '150.00',
                'rating': 4.8,
                'reviews': 156,
            },
            {
                'username': 'dr_rodriguez_oz',
                'email': 'srodriguez@ozoneparkmed.com',
                'first_name': 'Sofia',
                'last_name': 'Rodriguez',
                'specialty': 'Pediatrics',
                'license': 'NY-PED-234567',
                'experience': 10,
                'bio': 'Pediatrician dedicated to providing compassionate care for children. Expertise in developmental assessments and childhood illnesses.',
                'education': 'MD from Columbia University',
                'languages': 'English, Spanish, Portuguese',
                'fee': '140.00',
                'rating': 4.9,
                'reviews': 203,
            },
            {
                'username': 'dr_patel_oz',
                'email': 'apatel@ozoneparkmed.com',
                'first_name': 'Amit',
                'last_name': 'Patel',
                'specialty': 'Internal Medicine',
                'license': 'NY-IM-345678',
                'experience': 12,
                'bio': 'Internal medicine specialist focused on adult primary care and managing complex medical conditions.',
                'education': 'MD from Mount Sinai School of Medicine',
                'languages': 'English, Hindi, Gujarati',
                'fee': '160.00',
                'rating': 4.7,
                'reviews': 134,
            },
            {
                'username': 'dr_chen_oz',
                'email': 'lchen@ozoneparkmed.com',
                'first_name': 'Linda',
                'last_name': 'Chen',
                'specialty': 'Dermatology',
                'license': 'NY-DRM-456789',
                'experience': 8,
                'bio': 'Dermatologist specializing in medical and cosmetic dermatology. Expert in treating acne, eczema, and skin cancer screening.',
                'education': 'MD from Cornell Weill Medical College',
                'languages': 'English, Mandarin, Cantonese',
                'fee': '180.00',
                'rating': 4.8,
                'reviews': 178,
            },
            {
                'username': 'dr_williams_oz',
                'email': 'jwilliams@ozoneparkmed.com',
                'first_name': 'James',
                'last_name': 'Williams',
                'specialty': 'Cardiology',
                'license': 'NY-CAR-567890',
                'experience': 20,
                'bio': 'Cardiologist with extensive experience in heart disease prevention and treatment. Specializes in hypertension and heart failure management.',
                'education': 'MD from Johns Hopkins University',
                'languages': 'English',
                'fee': '200.00',
                'rating': 4.9,
                'reviews': 245,
            },
        ]

        providers = []
        for data in providers_data:
            # Create or get user
            user, user_created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'user_type': 'doctor',
                    'phone': '(718) 845-1234',
                    'is_email_verified': True,
                }
            )

            if user_created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'  ✓ Created user: {user.get_full_name()}')

            # Create or get provider profile
            provider, provider_created = Provider.objects.get_or_create(
                user=user,
                defaults={
                    'license_number': data['license'],
                    'years_experience': data['experience'],
                    'bio': data['bio'],
                    'education': data.get('education', ''),
                    'languages': data['languages'],
                    'average_rating': Decimal(str(data['rating'])),
                    'total_reviews': data['reviews'],
                    'accepting_new_patients': True,
                    'video_visit_available': True,
                    'is_verified': True,
                }
            )

            if provider_created:
                # Add specialty
                specialty = specialties[data['specialty']]
                provider.specialties.add(specialty)
                self.stdout.write(f'  ✓ Created provider: Dr. {user.get_full_name()}')

            # Create clinic affiliation
            affiliation, aff_created = ProviderClinicAffiliation.objects.get_or_create(
                provider=provider,
                clinic=clinic,
                defaults={
                    'is_primary': True,
                    'consultation_fee': Decimal(data['fee']),
                }
            )

            # Create availability (Mon-Fri, 9 AM - 5 PM)
            for day in range(5):  # Monday to Friday (0-4)
                ProviderAvailability.objects.get_or_create(
                    provider=provider,
                    clinic=clinic,
                    day_of_week=day,
                    defaults={
                        'start_time': '09:00',
                        'end_time': '17:00',
                        'is_active': True,
                    }
                )

            providers.append(provider)

        return providers
