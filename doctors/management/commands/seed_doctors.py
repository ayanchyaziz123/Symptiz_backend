from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from doctors.models import Specialty, Clinic, Doctor, DoctorClinicAffiliation, DoctorAvailability
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample doctor data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            DoctorAvailability.objects.all().delete()
            DoctorClinicAffiliation.objects.all().delete()
            Doctor.objects.all().delete()
            Clinic.objects.all().delete()
            Specialty.objects.all().delete()
            # Delete doctor users
            User.objects.filter(user_type='doctor').delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared'))

        self.stdout.write('Creating specialties...')
        specialties_data = [
            {'name': 'Family Medicine', 'icon': '👨‍⚕️', 'description': 'General healthcare for all ages'},
            {'name': 'Internal Medicine', 'icon': '🩺', 'description': 'Adult disease prevention and treatment'},
            {'name': 'Pediatrics', 'icon': '👶', 'description': 'Healthcare for infants, children, and adolescents'},
            {'name': 'Cardiology', 'icon': '❤️', 'description': 'Heart and cardiovascular system'},
            {'name': 'Dermatology', 'icon': '🧴', 'description': 'Skin, hair, and nail conditions'},
            {'name': 'Orthopedics', 'icon': '🦴', 'description': 'Bones, joints, and muscles'},
            {'name': 'Psychiatry', 'icon': '🧠', 'description': 'Mental health and behavioral disorders'},
            {'name': 'Gastroenterology', 'icon': '🫁', 'description': 'Digestive system disorders'},
            {'name': 'Neurology', 'icon': '🧬', 'description': 'Nervous system disorders'},
            {'name': 'Obstetrics & Gynecology', 'icon': '🤰', 'description': 'Women\'s reproductive health'},
        ]

        specialties = {}
        for spec_data in specialties_data:
            specialty, created = Specialty.objects.get_or_create(
                name=spec_data['name'],
                defaults={
                    'icon': spec_data['icon'],
                    'description': spec_data['description']
                }
            )
            specialties[spec_data['name']] = specialty
            if created:
                self.stdout.write(f'  Created specialty: {specialty.name}')

        self.stdout.write('Creating clinics...')
        clinics_data = [
            {
                'name': 'Community Health Center',
                'address': '123 Main Street',
                'city': 'Chicago',
                'state': 'IL',
                'zip_code': '60601',
                'phone': '(312) 555-0101',
                'email': 'info@communityhealthcenter.org',
                'clinic_type': 'community_center',
                'accepts_medicaid': True,
                'accepts_medicare': True,
                'sliding_scale': True,
                'free_services': False,
                'latitude': Decimal('41.8781'),
                'longitude': Decimal('-87.6298'),
            },
            {
                'name': 'Wellness Medical Group',
                'address': '456 Oak Avenue',
                'city': 'Chicago',
                'state': 'IL',
                'zip_code': '60602',
                'phone': '(312) 555-0102',
                'email': 'contact@wellnessmedical.com',
                'clinic_type': 'clinic',
                'accepts_medicaid': True,
                'accepts_medicare': True,
                'sliding_scale': True,
                'free_services': False,
                'latitude': Decimal('41.8801'),
                'longitude': Decimal('-87.6350'),
            },
            {
                'name': 'Children\'s Health Clinic',
                'address': '789 Elm Street',
                'city': 'Chicago',
                'state': 'IL',
                'zip_code': '60603',
                'phone': '(312) 555-0103',
                'email': 'info@childrenshealth.org',
                'clinic_type': 'clinic',
                'accepts_medicaid': True,
                'accepts_medicare': False,
                'sliding_scale': True,
                'free_services': True,
                'latitude': Decimal('41.8821'),
                'longitude': Decimal('-87.6400'),
            },
            {
                'name': 'Heart & Vascular Center',
                'address': '321 Pine Boulevard',
                'city': 'Chicago',
                'state': 'IL',
                'zip_code': '60604',
                'phone': '(312) 555-0104',
                'email': 'info@heartvascular.com',
                'clinic_type': 'hospital',
                'accepts_medicaid': True,
                'accepts_medicare': True,
                'sliding_scale': False,
                'free_services': False,
                'latitude': Decimal('41.8851'),
                'longitude': Decimal('-87.6250'),
            },
            {
                'name': 'Free Clinic of Chicago',
                'address': '555 Community Drive',
                'city': 'Chicago',
                'state': 'IL',
                'zip_code': '60605',
                'phone': '(312) 555-0105',
                'email': 'help@freeclinicchicago.org',
                'clinic_type': 'free_clinic',
                'accepts_medicaid': True,
                'accepts_medicare': True,
                'sliding_scale': True,
                'free_services': True,
                'latitude': Decimal('41.8771'),
                'longitude': Decimal('-87.6450'),
            },
        ]

        clinics = []
        for clinic_data in clinics_data:
            clinic, created = Clinic.objects.get_or_create(
                name=clinic_data['name'],
                defaults=clinic_data
            )
            clinics.append(clinic)
            if created:
                self.stdout.write(f'  Created clinic: {clinic.name}')

        self.stdout.write('Creating doctors...')
        doctors_data = [
            {
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah.johnson@example.com',
                'username': 'sjohnson',
                'specialty': 'Family Medicine',
                'years_experience': 12,
                'bio': 'Experienced family medicine physician dedicated to providing comprehensive healthcare.',
                'languages': 'English, Spanish',
                'clinic_index': 0,
                'fee': '75.00',
                'rating': 4.8,
                'reviews': 247,
            },
            {
                'first_name': 'Michael',
                'last_name': 'Chen',
                'email': 'michael.chen@example.com',
                'username': 'mchen',
                'specialty': 'Internal Medicine',
                'years_experience': 8,
                'bio': 'Internal medicine specialist focusing on preventive care and chronic disease management.',
                'languages': 'English, Mandarin',
                'clinic_index': 1,
                'fee': '0.00',
                'rating': 4.6,
                'reviews': 182,
            },
            {
                'first_name': 'Emily',
                'last_name': 'Rodriguez',
                'email': 'emily.rodriguez@example.com',
                'username': 'erodriguez',
                'specialty': 'Pediatrics',
                'years_experience': 10,
                'bio': 'Pediatrician with a passion for child development and preventive care.',
                'languages': 'English, Spanish',
                'clinic_index': 2,
                'fee': '50.00',
                'rating': 4.9,
                'reviews': 324,
            },
            {
                'first_name': 'James',
                'last_name': 'Wilson',
                'email': 'james.wilson@example.com',
                'username': 'jwilson',
                'specialty': 'Cardiology',
                'years_experience': 15,
                'bio': 'Cardiologist specializing in heart disease prevention and treatment.',
                'languages': 'English',
                'clinic_index': 3,
                'fee': '0.00',
                'rating': 4.7,
                'reviews': 198,
            },
            {
                'first_name': 'Jennifer',
                'last_name': 'Lee',
                'email': 'jennifer.lee@example.com',
                'username': 'jlee',
                'specialty': 'Dermatology',
                'years_experience': 9,
                'bio': 'Board-certified dermatologist treating all skin conditions.',
                'languages': 'English, Korean',
                'clinic_index': 1,
                'fee': '85.00',
                'rating': 4.8,
                'reviews': 215,
            },
            {
                'first_name': 'Robert',
                'last_name': 'Martinez',
                'email': 'robert.martinez@example.com',
                'username': 'rmartinez',
                'specialty': 'Orthopedics',
                'years_experience': 11,
                'bio': 'Orthopedic surgeon specializing in sports medicine and joint replacement.',
                'languages': 'English, Spanish',
                'clinic_index': 3,
                'fee': '100.00',
                'rating': 4.6,
                'reviews': 167,
            },
            {
                'first_name': 'Amanda',
                'last_name': 'Foster',
                'email': 'amanda.foster@example.com',
                'username': 'afoster',
                'specialty': 'Psychiatry',
                'years_experience': 7,
                'bio': 'Psychiatrist providing compassionate mental health care.',
                'languages': 'English',
                'clinic_index': 0,
                'fee': '65.00',
                'rating': 4.9,
                'reviews': 289,
            },
            {
                'first_name': 'David',
                'last_name': 'Kim',
                'email': 'david.kim@example.com',
                'username': 'dkim',
                'specialty': 'Gastroenterology',
                'years_experience': 13,
                'bio': 'Gastroenterologist treating digestive system disorders.',
                'languages': 'English, Korean',
                'clinic_index': 3,
                'fee': '90.00',
                'rating': 4.7,
                'reviews': 203,
            },
        ]

        for doctor_data in doctors_data:
            # Create user for doctor
            user, user_created = User.objects.get_or_create(
                username=doctor_data['username'],
                defaults={
                    'email': doctor_data['email'],
                    'first_name': doctor_data['first_name'],
                    'last_name': doctor_data['last_name'],
                    'user_type': 'doctor',
                    'is_email_verified': True,
                }
            )

            if user_created:
                user.set_password('password123')
                user.save()

            # Create doctor profile
            doctor, doctor_created = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'license_number': f'MD{random.randint(100000, 999999)}',
                    'years_experience': doctor_data['years_experience'],
                    'bio': doctor_data['bio'],
                    'languages': doctor_data['languages'],
                    'average_rating': Decimal(str(doctor_data['rating'])),
                    'total_reviews': doctor_data['reviews'],
                    'accepting_new_patients': True,
                    'video_visit_available': random.choice([True, False]),
                    'is_verified': True,
                }
            )

            if doctor_created:
                # Add specialty
                specialty = specialties[doctor_data['specialty']]
                doctor.specialties.add(specialty)

                # Add clinic affiliation
                clinic = clinics[doctor_data['clinic_index']]
                DoctorClinicAffiliation.objects.create(
                    doctor=doctor,
                    clinic=clinic,
                    is_primary=True,
                    consultation_fee=Decimal(doctor_data['fee'])
                )

                # Add availability schedule (Mon-Fri, 9AM-5PM)
                for day in range(5):  # Monday to Friday
                    DoctorAvailability.objects.create(
                        doctor=doctor,
                        clinic=clinic,
                        day_of_week=day,
                        start_time='09:00',
                        end_time='17:00',
                        is_active=True
                    )

                self.stdout.write(f'  Created doctor: Dr. {user.get_full_name()}')

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully seeded database with:'))
        self.stdout.write(self.style.SUCCESS(f'  - {Specialty.objects.count()} specialties'))
        self.stdout.write(self.style.SUCCESS(f'  - {Clinic.objects.count()} clinics'))
        self.stdout.write(self.style.SUCCESS(f'  - {Doctor.objects.count()} doctors'))
        self.stdout.write(self.style.SUCCESS(f'  - {DoctorClinicAffiliation.objects.count()} clinic affiliations'))
        self.stdout.write(self.style.SUCCESS(f'  - {DoctorAvailability.objects.count()} availability slots'))
