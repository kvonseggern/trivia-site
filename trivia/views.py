from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.forms import modelformset_factory, inlineformset_factory
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView

from .models import (
    FinalResponse, Game, Round, Question,
    Response, DoubleRound, FinalRound
)
from .forms import ResponseForm

# Create your views here.

# A few functions for use later on. ######################

def staff_check(user):
    return user.is_staff

# Begin game management views #############################

class IndexView(generic.TemplateView):
    template_name = 'trivia/index.html'


class GameIndexView(generic.ListView): # pylint: disable=too-many-ancestors
    '''List of games for the players to get into'''
    model = Game


class GameDetailView(generic.DetailView):
    '''Main landing page and public scoreboard for a game'''
    model = Game
    title = 'Game Detail'


class RoundDetailView(LoginRequiredMixin, generic.DetailView):
    model = Round


@login_required
def response_view(request, **kwargs):
    try:
        # if the response has been created, grab it
        obj = Response.objects.get(player=request.user, question_id=kwargs['question'])
    except Response.DoesNotExist:
        # if the question hasn't been answered, create a new object
        obj = Response.objects.create(player=request.user, question_id=kwargs['question'])
    if obj.question.round.status != '1':
        raise PermissionDenied("The round status doesn't allow that")
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ResponseForm(request.POST, instance=obj)
        # check whether it's valid:
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse('trivia:round_detail', args=(kwargs['round'],))
            )
    else:
        form = ResponseForm(instance=obj)
    return render(request, 'trivia/response_form.html', {'form': form, **kwargs})


@login_required
def check_answers(request, **kwargs):
    '''
    Page to have a user check another user's answers.
    Done only during the 'check answers' round status.
    Trivia master has access at all times.
    '''
    round_obj = Round.objects.get(id=kwargs['round'])
    if round_obj.status != '2' and not request.user.is_staff:
        raise PermissionDenied("It's not time to check the round!")
    params = {'player__id': kwargs['player'], 'question__round__id': kwargs['round']}
    q_set = Response.objects.filter(**params)
    ResponseFormSet = modelformset_factory(
        Response, fields=('correct',), extra=0,
    )
    if request.method == "POST":
        formset = ResponseFormSet(
            request.POST, request.FILES, queryset=q_set,
        )
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(
                reverse('trivia:game_detail', kwargs={'pk': kwargs['game']})
            )
    else:
        formset = ResponseFormSet(queryset=q_set)
    kwargs['formset'] = formset
    kwargs['responses'] = q_set
    kwargs['player'] = User.objects.get(id=kwargs['player'])
    if kwargs['player'] == request.user and not request.user.is_staff:
        raise Http404("Do you think I'm going to let you check your own answers?")
    return render(request, 'trivia/check_answers.html', kwargs)


class RoundStatusUpdate(UserPassesTestMixin, UpdateView):
    model = Round
    template_name = 'trivia/round_form.html'
    fields = ['status']

    def test_func(self):
        return self.request.user.is_staff


class FinalRoundStatusUpdate(UserPassesTestMixin, UpdateView):
    model = FinalRound
    template_name = 'trivia/finalround_form.html'
    fields = ['status']

    def test_func(self):
        return self.request.user.is_staff


class FinalRoundWagerUpdate(UpdateView):
    model = FinalResponse
    fields = ['wager']
    template_name = 'trivia/wager_form.html'

    def post(self, request, *args, **kwargs):
        final_round = FinalRound.objects.get(finalresponse__id=self.kwargs['pk'])
        if final_round.status != '1':
            messages.error(request, 'The time to wager has passed! Your wager did not get updated.')
            return HttpResponseRedirect(
                reverse('trivia:game_detail', kwargs={'pk': final_round.game_id})
            )
        return super().post(request, *args, **kwargs)


@login_required
def finalwager(request, **kwargs):
    final_round = FinalRound.objects.get(game_id=kwargs['game'])
    try:
        obj = FinalResponse.objects.get(final_round=final_round, player=request.user)
    except FinalResponse.DoesNotExist:
        # Create a final answer object if it does not already exist
        obj = FinalResponse.objects.create(final_round=final_round, player=request.user)
        obj.save()
    return HttpResponseRedirect(reverse('trivia:final_wager_update', kwargs={'pk': obj.id}))


class FinalAnswerUpdate(UpdateView):
    model = FinalResponse
    fields = ['response']
    template_name = 'trivia/final_answer.html'


@login_required
def finalanswer(request, **kwargs):
    try:
        # Find the FinalAnswer object for the user and redirect to the update view
        final_answer = FinalResponse.objects.get(player=request.user, final_round__game_id=kwargs['game'])
        return HttpResponseRedirect(
            reverse('trivia:final_answer_update', kwargs={'pk': final_answer.id})
        )
    except FinalResponse.DoesNotExist:
        raise PermissionDenied("You didn't get a wager in. Take it up with the trivia master.")


@login_required
def manage_finalanswers(request, **kwargs):
    FinalFormSet = inlineformset_factory(
        FinalRound, FinalResponse, fields=('correct',), can_delete=False, extra=0
    )
    if request.method == "POST":
        formset = FinalFormSet(
            request.POST, request.FILES, instance=FinalRound.objects.get(game_id=kwargs['game']),
        )
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(
                reverse('trivia:game_detail', kwargs={'pk': kwargs['game']})
            )
    else:
        formset = FinalFormSet(instance=FinalRound.objects.get(game_id=kwargs['game']))
    kwargs['formset'] = formset
    kwargs['final_answers'] = FinalResponse.objects.filter(final_round__game_id=kwargs['game'])
    return render(request, 'trivia/finalanswer_check.html', kwargs)


class RoundReviewDetail(UserPassesTestMixin, generic.DetailView):
    '''Shows the answers of all players after the round is over.'''
    model = Round
    template_name = 'trivia/round_review.html'

    def test_func(self):
        # Gives trivia master access at all times, everyone else only after the round is over.
        if Round.objects.get(id=self.kwargs['pk']).status == '3':
            return self.request.user.is_authenticated
        return self.request.user.is_staff


# Double round success message:
DR_MSG = 'Your double round is: %(round)s'

def doubleround_view(request, *args, **kwargs):
    try:
        double_round = DoubleRound.objects.get(player=request.user, game__id=kwargs['game']) 
    except DoubleRound.DoesNotExist:
        double_round = DoubleRound.objects.create(player=request.user, game_id=kwargs['game'])
        double_round.save()
    return HttpResponseRedirect(
        reverse('trivia:double_update', args=(double_round.id,))
    )


class DoubleRoundUpdate(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = DoubleRound
    fields = ['round']
    template_name = 'trivia/doubleround_form.html'
    success_message = DR_MSG

    def get_context_data(self, **kwargs):
        # This object filters down the list to only rounds in the relevant game
        obj = Round.objects.filter(game_id=self.object.game_id)
        context = super().get_context_data(**kwargs)
        context['form'].fields['round'].queryset = obj
        return context

    def test_func(self):
        # Gives trivia master access at all times, everyone else only after the round is over.
        if DoubleRound.objects.get(id=self.kwargs['pk']).game.round_status_sum() == 0:
            return self.request.user.is_authenticated
        return self.request.user.is_staff


# Management Views Below #################################

class ManageView(UserPassesTestMixin, generic.TemplateView):
    '''Starting view for trivia master management'''
    template_name = 'trivia/manage.html'

    def test_func(self):
        return user.is_staff


class RoundCreate(UserPassesTestMixin, CreateView):
    model = Round
    fields = ['category_text', 'game']

    def get_success_url(self):
        return reverse('trivia:manage_questions', kwargs={'round_pk': self.object.pk})

    def test_func(self):
        return user.is_staff


@user_passes_test(staff_check)
def manage_questions(request, round_pk):
    round_obj = Round.objects.get(id=round_pk)
    QuestionInlineFormSet = inlineformset_factory(
        Round, Question, fields=('question', 'answer', 'alt_answers',), extra=10
    )
    if request.method == "POST":
        formset = QuestionInlineFormSet(request.POST, request.FILES, instance=round)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('trivia:manage'))
    else:
        formset = QuestionInlineFormSet(instance=round_obj)
    return render(request, 'trivia/manage_questions.html', {'formset': formset})


# Begin Signup View ######################################

def signup(request):
    '''The signup view to create a new user'''
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, 'Account created successfully. You are now logged in.')
            return redirect('trivia:index')
    else:
        form = UserCreationForm()
    return render(request, 'trivia/signup.html', {'form': form})
