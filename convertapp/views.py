from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
import speech_recognition as sr
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, HttpResponse
from .models import Project, Conversation, Text, User
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
import arabic_reshaper
from bidi.algorithm import get_display
from pocketsphinx import pocketsphinx, Jsgf, FsgModel
from django.contrib import messages  # Import Django's messages framework
from django.db import IntegrityError

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error_message_l = 'Invalid username or password.' # Add an error message
        # If there are errors, pass them to the template
        return render(request, 'index.html', {'error_message_l': error_message_l})


    return render(request, 'index.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 == password2:
            try:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                user = authenticate(request, username=username, password=password1)
                if user is not None:
                    login(request, user)
                    return redirect('index')  # Redirect to a success page
                else:
                    error_message = 'Failed to log in after signup'
            except Exception as e:
                error_message = f'Signup failed: {str(e)}'
        else:
            error_message = 'Passwords do not match'
        
        # If there are errors, pass them to the template
        return render(request, 'index.html', {'error_message': error_message})

    return render(request, 'index.html')

#  Logout page  ===============================================================================
def logoutPage(request):
    logout(request)
    return redirect('index')

def index(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Retrieve all projects for the logged-in user
        projects = Project.objects.filter(user=request.user)

        # Check if any projects exist for the user
        projects_exist = projects.exists()

        # Get the active project if it exists (You can modify this based on your logic)
        active_project = projects.filter(active=True).first()

        return render(request, 'index.html', {
            'projects_exist': projects_exist,
            'active_project': active_project,
        })
    else:
        # For unauthenticated users, return the index.html template without any project-related context
        return render(request, 'index.html')
 
@login_required
def update_profile_and_password(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            # Profile update logic
            user = request.user
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.save()
            messages.success(request, 'Profile updated successfully.')

        elif 'update_password' in request.POST:
            # Password update logic
            user = request.user
            current_password = request.POST['current_password']
            new_password = request.POST['new_password']
            confirm_password = request.POST['confirm_password']

            if user.check_password(current_password) and new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Update the session to prevent log out
                messages.success(request, 'Password updated successfully.')

    return redirect(request.META.get('HTTP_REFERER', 'profile'))

@login_required
def Gestion_workspaces(request):
    # Get all projects for the currently logged-in user
    if request.user.is_authenticated:
        user_projects = Project.objects.filter(user=request.user).order_by('name')
    else:
        user_projects = None
    
    context = {
        'user_projects': user_projects,
    }
    
    return render(request, 'Gestion_workspaces.html', context)

@login_required
def fetch_projects(request):
    page_number = request.GET.get('page', 1)
    projects_per_page = 3 if request.GET.get('small_screen') == 'true' else 6

    projects = Project.objects.all().filter(user = request.user)
    
    paginator = Paginator(projects, projects_per_page)
    page = paginator.get_page(page_number)
    
    projects_data = [{'name': project.name, 'id': project.id} for project in page]
    
    has_next = page.has_next()

    return JsonResponse({'projects': projects_data, 'has_next': has_next})

@login_required
def create_project(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        user = request.user
        projects_count = Project.objects.filter(user=user).count()
        project_name = f"Untitled {projects_count + 1}"

        # Create the new project in the database
        project = Project.objects.create(name=project_name, user=user)

        # Store the selected language in the user's session
        request.session['language'] = language

        # Redirect the user to the newly created project page
        return redirect(reverse('workspace', kwargs={'project_id': project.id}))

    return redirect('workspace')

@login_required
def delete_project(request, project_id):
    # Check if the request method is DELETE
    if request.method == 'DELETE':
        # Assuming you want to require user authentication to delete a project
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required to delete a project.'}, status=401)
        
        # Get the project to be deleted, or return a 404 response if it doesn't exist
        project = get_object_or_404(Project, id=project_id, user=request.user)
        
        # Delete the project
        project.delete()
        
        # Return a success response
        return HttpResponse(status=204)  # 204 No Content
        
    # If the request method is not DELETE, return a method not allowed response
    return HttpResponse(status=405)  # 405 Method Not Allowed

@login_required
def update_project_name(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id, user=request.user)
        new_project_name = request.POST.get('projectName')
        project.name = new_project_name
        project.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

@login_required
def workspace(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # language = request.GET.get('language', 'en-US')
    language = request.session.get('language', 'en-US')
    conversation_id = request.GET.get('conversation_id')

    conversations = Conversation.objects.filter(project=project).order_by('-sequence_number')

    selected_conversation = None  # Define selected_conversation outside of the if block
    
    if request.method == 'POST':
        if 'audioFile' in request.FILES:
            r = sr.Recognizer()
            audio_file = request.FILES['audioFile']
            with sr.AudioFile(audio_file) as source:
                audio = r.record(source)
            
            # Recognize the audio
            text = r.recognize_google(audio, language=language)
            
            # Check if the recognized text is not empty
            if text.strip():  # Check if the text contains non-whitespace characters
                # Check if there's a selected conversation, create a new one if not
                if conversation_id:
                    selected_conversation = get_object_or_404(Conversation, id=conversation_id, project=project)
                else:
                    selected_conversation = Conversation.objects.filter(project=project).order_by('-sequence_number').first()
                    if not selected_conversation:
                        selected_conversation = Conversation.objects.create(project=project)

                Text.objects.create(conversation=selected_conversation, text_content=text)

        if 'recognized_text_hidden' in request.POST:
            recognized_text_hidden = request.POST['recognized_text_hidden']
            
            # Check if the recognized text is not empty
            if recognized_text_hidden.strip():  # Check if the text contains non-whitespace characters
                # Check if there's a selected conversation, create a new one if not
                if conversation_id:
                    selected_conversation = get_object_or_404(Conversation, id=conversation_id, project=project)
                else:
                    selected_conversation = Conversation.objects.filter(project=project).order_by('-sequence_number').first()
                    if not selected_conversation:
                        selected_conversation = Conversation.objects.create(project=project)

                Text.objects.create(conversation=selected_conversation, text_content=recognized_text_hidden)

        if selected_conversation:
            return redirect(f'/workspace/{project_id}/?conversation_id={selected_conversation.id}&success=true')
        else:
            selected_conversation = Conversation.objects.filter(project=project).order_by('-sequence_number').first()
            return redirect(f'/workspace/{project_id}/?conversation_id={selected_conversation.id}&success=true')
    
    else:
        if conversation_id:
            selected_conversation = get_object_or_404(Conversation, id=conversation_id, project=project)

    return render(request, 'workspace.html', {
        'project': project,
        'language': language,
        'conversations': conversations,
        'selected_conversation': selected_conversation,
    })

@login_required
def start_new_conversation(request):
    if request.method == 'POST':
        project_id = request.POST.get('projectId')

        try:
            project = Project.objects.get(id=project_id)

            # Create a new conversation
            conversation = Conversation.objects.create(project=project)
            
            # Return the conversation ID in the response
            return JsonResponse({'success': True, 'conversationId': conversation.id})
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Project not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def update_language(request):
    if request.method == 'POST':
        new_language = request.POST.get('language')
        request.session['language'] = new_language
    return redirect(request.META.get('HTTP_REFERER'))

def test(request):
    return render(request, 'test.html')







"""

def profile_m(request):
    return render(request, 'profile_m.html')

# test
def project_detaille_t(request):
    return render(request, 'project_detaille_t.html')

def project_detaill(request):
    return render(request, 'project_detaill.html')

def test(request):
    return render(request, 'test.html')

# def create_project(request):
#     if request.method == 'POST':
#         language = request.POST.get('language')
#         user = request.user
#         projects_count = Project.objects.filter(user=user).count()
#         project_name = f"Untitled {projects_count + 1}"

#         # Create the new project in the database
#         project = Project.objects.create(name=project_name, user=user)

#         # Redirect the user to the newly created project page with language as a query parameter
#         return redirect(f'/project/{project.id}/?language={language}')

#     return redirect('project_detail')

# Function that update_project_name

#== English ====================================================================    En
def english_convert_audio(request):
    if request.method == 'POST':
        r = sr.Recognizer()
        audio_file = request.FILES['audioFile']
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="en-US")

        # Get the current user's active project or create a new one if it doesn't exist
        project = Project.objects.filter(user=request.user, active=True).first()
        if not project:
            project = Project.objects.create(name='My Project', user=request.user, active=True)

        # Create a new conversation for the user in the active project
        conversation = Conversation.objects.create(project=project)

        # Create a new text entry for the conversation with the recognized text
        Text.objects.create(conversation=conversation, text_content=text)

        return render(request, 'english_convert_audio.html', {'text': text, 'project': project})
    return render(request, 'english_convert_audio.html')
# def english_convert_audio(request):
#     if request.method == 'POST':
#         r = sr.Recognizer()
#         audio_file = request.FILES['audioFile']
#         with sr.AudioFile(audio_file) as source:
#             audio = r.record(source)
#         text = r.recognize_google(audio, language="en-US")

#         return render(request, 'english_convert_audio.html', {'text': text})
#     return render(request, 'english_convert_audio.html')


def recognize_speech_eng(request):
    r = sr.Recognizer()

    def process_audio(stream):
        chunks = []
        for chunk in stream:
            r.adjust_for_ambient_noise(chunk)
            try:
                text = r.recognize_sphinx(chunk)
                print("Recognized: {}".format(text))
                chunks.append(text)
            except sr.UnknownValueError:
                print("Could not understand audio")
        return ' '.join(chunks)  # Concatenate the recognized text chunks

    with sr.Microphone() as source:
        audio_stream = sr.MicrophoneStream(source)
        text = process_audio(audio_stream)

    return render(request, 'english_convert_audio.html', {'text': text})

#== Frensh =====================================================================    Fr
def frensh_convert_audio(request):
    if request.method == 'POST':
        r = sr.Recognizer()
        audio_file = request.FILES['audioFile']
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="fr-FR")

        return render(request, 'frensh_convert_audio.html', {'text': text})
    return render(request, 'frensh_convert_audio.html')


def recognize_speech_fr(request):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        text = ""
        while True:
            try:
                audio = r.listen(source)
                text = r.recognize_google(audio)
                print("You said: {}".format(text))
                break
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))

    return render(request, 'frensh_convert_audio.html', {'text': text})
#== Arabic =====================================================================    Ar
def arabic_convert_audio(request):
    if request.method == 'POST':
        r = sr.Recognizer()
        audio_file = request.FILES['audioFile']
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="ar-AR")

        return render(request, 'arabic_convert_audio.html', {'text': text})
    return render(request, 'arabic_convert_audio.html')


def recognize_speech_ar(request):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        text = ""
        while True:
            try:
                audio = r.listen(source)
                text = r.recognize_google(audio)
                print("You said: {}".format(text))
                break
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))

    return render(request, 'arabic_convert_audio.html', {'text': text})
#== Tamazight ==================================================================    Ta

def tamazight_convert_audio(request):
    if request.method == 'POST':
        r = sr.Recognizer()
        audio_file = request.FILES['audioFile']
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="'fr-FR")

        return render(request, 'tamazigh_convert_audio.html', {'text': text})
    return render(request, 'tamazigh_convert_audio.html')


def recognize_speech_ta(request):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        text = ""
        while True:
            try:
                audio = r.listen(source)
                text = r.recognize_google(audio)
                print("You said: {}".format(text))
                break
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))

    return render(request, 'tamazigh_convert_audio.html', {'text': text})

"""