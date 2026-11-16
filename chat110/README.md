# Chat110: Choose What an AI Writes Next

Chat110 puts you in charge of a core step in how language models generate
text: **choosing what comes next**. You will implement **decoding algorithms**,
the procedures that turn a model's predictions into the next piece of a
reply. This is the same kind of decision made by the large language models
behind ChatGPT and Claude.

A **language model** is a program trained to predict text from the text that
came before it. You may have heard the abbreviation **LLM**, which stands for
*large language model*. A **prompt** is the text you give the model to respond
to. The pieces of text it predicts are called **tokens**.

Your functions will work with **a real, trained language model running on
your laptop**: Gemma, created by Google. Gemma supplies a score for each
possible next token, and your function chooses one. The provided program
adds that choice to the conversation, asks Gemma for new scores, and calls
your function again. When you chat using a completed stage, **your code
selects every generated token in the reply**.

You will begin by always choosing the highest score. Then you will turn the
scores into probabilities, use those probabilities to make a random choice,
and limit which choices are available. These are standard approaches to
LLM decoding, built from the lists, loops, conditionals, and functions you
already know. By the end, you can demonstrate how your own Python code helps
a language model turn predictions into a conversation.

This exercise has **two parts**, each with its own Gradescope assignment and
due date:

| Part | Stages | Graded work |
| --- | --- | --- |
| [Part 1: Tokens and probabilities](#part-1-tokens-and-probabilities) | 0–2 | Stages 1 and 2, 50 points each; Stage 0 is a supplied warm-up |
| [Part 2: Sampling and top-p](#part-2-sampling-and-top-p) | 3–4 | Stages 3 and 4, 50 points each, building on your Part 1 helpers |

Check each Gradescope assignment for its deadline. Both parts use the same
submission bundle; each grader evaluates only the stages for its part.

## Meet the model

This exercise uses **Gemma 3 270M IT**, a language model created and distributed
by **Google DeepMind**. The **270M** means approximately **270 million
parameters**: numbers learned during training that shape the model's
predictions. **IT** stands for *instruction-tuned*, meaning the model received
additional training to respond to instructions. You can read more in
[Google's introduction to Gemma 3 270M](https://developers.googleblog.com/en/introducing-gemma-3-270m/).

Gemma is **open weight**: Google makes its trained model weights available to
download, so we can run the model on our own computers. This project uses
[Google's published model](https://huggingface.co/google/gemma-3-270m-it)
under the [Gemma terms](MODEL_USE.md). Once downloaded, the model generates
replies locally on your computer.

Our model is tiny compared with **frontier models**, the most capable general
purpose models. For scale, [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3)
has **671 billion total parameters**, about **2,500 times as many** as our
0.27-billion-parameter Gemma. Gemma's small size makes it practical for this
laptop-based exercise, though its replies will be much less capable than those
of the leading AI assistants you use today. It still lets us explore the same core
process powering ChatGPT and Claude: choosing the next token, one token at a time.

## Get started in the workspace

Open `workspace.code-workspace` in VS Code.

1. Select **Terminal > Run Task**.
2. Select **Sync all workspace projects** for the `support` folder.
3. Follow the terminal messages while dependencies are installed.

`chat110` should appear as a top-level folder in Explorer. Student programs
are in `src/decoders/`. The provided runtime and setup files are hidden in
Explorer so you can focus on your work.

Open a terminal for the `chat110` folder. All commands in this guide run there.
To install or check only this project's dependencies, run:

```text
uv sync --locked --managed-python
```

Stage 0 uses the real model. Running it or a chat command for the first time
downloads a verified model bundle and reuses it for later runs. The small
examples in Stages 1–4 use only Python and a few numbers; they do not load the
model. Allow about 1 GB free for downloading
and unpacking. See the [model-use information](MODEL_USE.md),
[Gemma terms](licenses/GEMMA_TERMS_OF_USE.md), and
[prohibited-use policy](licenses/GEMMA_PROHIBITED_USE_POLICY.md) for Google's
licensing terms.

## Quick VS Code tasks

Use **Terminal > Run Task** in the `chat110` folder for:

- **Chat110: Inspect Token Scores** — run the supplied Stage 0 warm-up.
- **Chat110: Chat with a Completed Stage** — select Stage 1–4 after implementing it.
- **Create Chat110 Submission** — create the timestamped Gradescope ZIP.

## Learning goals

By the end of this exercise, you will be able to:

- explain how LLMs such as those behind ChatGPT and Claude generate text one
  token at a time, distinguishing the model's predictions from the decoding
  algorithm's choices;
- implement decoding strategies that control a real language model's replies,
  from greedy selection to weighted sampling with top-p filtering;
- explain how probability and randomness shape responses, including why a
  likely continuation is not necessarily a factually correct one;
- build a larger algorithm by composing reusable functions with clear inputs
  and outputs, checking each building block before connecting them; and
- design controlled experiments to compare decoding strategies, using fixed
  prompts and repeatable randomness to interpret differences across runs.

## The decoding progression

A **decoding algorithm** is the procedure that chooses the next token from the
model's scores. A **token** is one entry in the model's vocabulary. It can
represent a word, part of a word, punctuation, or a special marker such as the
end of a reply. A token is not necessarily a whole word.

Across the two parts, you will work through a warm-up and four stages:

- **Stage 0:** Tokenize a prompt and inspect its ten highest-scoring next tokens,
  connecting each token's text, ID, and score.
- **Stage 1:** Choose the token with the largest score. This is called
  **greedy decoding**.
- **Stage 2:** Convert scores into probabilities. Keep choosing the largest
  value so you can examine this new representation before using it differently.
- **Stage 3:** Use the probabilities to make a random choice. More likely
  tokens should have a greater chance of being selected.
- **Stage 4:** Keep a group of likely candidates before making
  the random choice. This is called **top-p sampling**.

Stages 1 through 4 can each drive a real conversation with Gemma, the language
model provided with this project.

## Before you begin

Your work belongs in these files:

```text
src/decoders/stage_00_inspect.py
src/decoders/stage_01_greedy.py
src/decoders/stage_02_softmax.py
src/decoders/stage_03_sampling.py
src/decoders/stage_04_top_p.py
```

Stage 0 is a supplied warm-up. Stages 1–4 contain typed function signatures
and short TODO prompts. Use the function requirements and worked examples
below to design your algorithms, replacing each `raise NotImplementedError(...)`
with your implementation. Keep the supplied imports. Add your own calls in
the `if __name__ == "__main__":` block to check your functions against the
small examples, replacing its `pass` placeholder. Work in the file for the
current stage and preserve your earlier versions so you can compare them.
When a later stage reuses a helper, copy your completed helper into that stage
file. Each stage should work independently.

Read Stages 1–4 from the top down: `next_token` introduces the overall decision,
followed by its helpers in the order of the decoding steps. The shared
`normalize` helper comes last. Python looks up helper functions when they are
called, so their definitions can appear below the functions that use them.
The demonstration block stays at the bottom, after all function definitions.

Replace `__author__: str = "Your PID goes here."` in each of Stages 1–4 with
your nine-digit PID as a string. Stages 1 and 2 are your graded work for
Part 1; Stages 3 and 4 are your graded work for Part 2.
Calling an unfinished function raises `NotImplementedError`; this is a
reminder to complete that function before trying chat.

Keep a module docstring describing each file and a function docstring describing
each function. Annotate your parameters, return types, and variables. Use loops
for the searches and running totals in this exercise so you can practice how
those algorithms work.

We provide support files and the program that runs the model. You do not need to
edit them. You may assume the functions receive valid inputs: dictionaries and
score lists are nonempty, scores are finite numbers, and probability lists add
up to approximately `1.0`. Later sections explain the inputs to each helper.

## Part 1: Tokens and probabilities

Explore the supplied Stage 0 warm-up, then implement Stages 1 and 2.

### Meet the next-token interface

In class, we built a
small language model from sentences such as `the cat sat on the mat`. Imagine
continuing this unfinished sentence:

```text
The cat sat on the
```

Our class model used the final word, `the`, to look up a list of possible next
words. Repeated entries made some words more likely when we used
`random.choice`: the list acted like a weighted die. In contrast, an LLM like Gemma uses the whole
input sequence to calculate scores for possible next tokens. Our job is to
turn those scores into a choice.

#### From text to token IDs

A **tokenizer** translates text into token IDs and decodes those IDs back into
text. Our [Gemma 3 270M IT model](https://huggingface.co/google/gemma-3-270m-it/tree/ac82b4e820549b854eebf28ce6dedaf9fdfa17b3)
encodes the text above as five tokens:

```text
Text pieces: ["The", " cat", " sat", " on", " the"]
Token IDs:   [818,   5866,   2838,   580,   506]
```

Each ID matches the text piece at the same position. Joining the pieces gives
back exactly `The cat sat on the`, including the spaces. The tokenizer also
prepends `<bos>` (ID `2`), which stands for **beginning of sequence**, so the model receives
`[2, 818, 5866, 2838, 580, 506]` for this example.

Our class model had a vocabulary of nine words. Gemma has **262,144 token IDs
in its output vocabulary**, including words, word pieces, punctuation, and
special markers. Here is a small subset:

| Token ID | Token spelling | What it represents |
| --- | --- | --- |
| `818` | `The` | A whole word |
| `5866` | `▁cat` | A space followed by a word |
| `1854` | `ization` | A word piece, as in `token` + `ization` |
| `236761` | `.` | Punctuation |
| `107` | `\n` | A newline character |
| `2` | `<bos>` | A special marker for the beginning of a sequence |
| `106` | `<end_of_turn>` | A special marker for the end of a conversational turn |

In the tokenizer's spelling, `▁` represents a space; it does not appear as that
symbol in the decoded text. The `\n` above is Python's notation for a newline.
Special markers structure the conversation and are normally hidden from the
displayed reply. A token can therefore represent more or less than one word.

#### From token IDs to scores

Gemma starts with your **prompt**: the text you give it, such as
`The cat sat on the`. As it writes, the text generated so far becomes part of
the input too. In a conversation, earlier messages also provide context.
This process is called **autoregressive generation**. The fancy term simply
means predicting one token at a time, adding it to the text, and using that
updated text to predict the next token.

Gemma uses the token IDs for this text to produce one **logit** for each of its
262,144 possible next-token IDs. A logit is a raw score expressing how strongly
the model favors a token in this context. A larger score means a stronger
preference. Our runner puts the scores into a dictionary: each key is a token
ID, and each value is its logit.

Here are the **five highest actual scores** for our unfinished sentence,
rounded to three decimal places and shown from highest to lowest:

```python
top_five_logits: dict[int, float] = {
    191646: 43.392,  # " windowsill"
    1756: 41.113,    # " mat"
    4771: 39.803,    # " window"
    120926: 39.800,  # " armchair"
    27210: 39.632,   # " sofa"
}
```

This is only a preview; the dictionary your function receives contains all
262,144 scores. These values were measured with our pinned Gemma model
continuing `<bos>The cat sat on the` directly. The chat runner adds message
formatting, so entering the same words in chat gives a different input and
can produce different scores.

**A logit is not a probability.** The score `43.392` does not mean a 43.392%
chance. Logits can be positive, zero, or negative, and they do not have to sum
to one. They are also not the occurrence counts we used in class.

#### From scores to probabilities to a choice

In class, we divided counts by their total to obtain probabilities. For
Gemma's scores, we use **softmax**: turn the logits into positive relative
weights, then divide each weight by the total. You will implement this recipe
in Stage 2.

Applying softmax to **all 262,144 scores** gives these probabilities for the
same five tokens, rounded for display:

| Next text piece | Probability |
| --- | --- |
| `" windowsill"` | 71.22% |
| `" mat"` | 7.29% |
| `" window"` | 1.97% |
| `" armchair"` | 1.96% |
| `" sofa"` | 1.66% |
| All other tokens combined | 15.90% |

The other tokens still have a share of the probability. Applying softmax to
only the five displayed logits would give different probabilities.

When you implement Stages 1 and 2, you will write code that makes a **greedy**
choice: always choose the next token the model considers most probable.
You will find it using the highest score in Stage 1 and the highest
probability in Stage 2. For this example, both implementations will select
`191646`, the ID for `" windowsill"`, every time they receive these scores.
In Stage 3, you will implement
**weighted sampling**, the same weighted-die idea from class: draw a random
number and use the probabilities to choose a token. `" windowsill"` has about
a 71% chance, while `" mat"` has about a 7% chance. In Stage 4, you will add a
filter that keeps a smaller group of likely candidates before sampling.

#### Your function makes the choice

Every choosing stage defines the same function:

```python
def next_token(logits: dict[int, float]) -> int:
    """Choose and return a token ID from the supplied scores."""
```

The input is the dictionary of token IDs and logits. The return value is one
token ID, such as `191646`. Our runner knows which text belongs to that ID;
your function only needs to choose it. The examples above and Stage 0 use real
Gemma IDs and scores. The small examples in Stages 1–4 use invented IDs and
scores to make the algorithms easier to trace.

#### How one choice becomes a reply

After a choice, the runner repeats these steps:

1. Ask the model for scores for the next token.
2. Pass those scores to your `next_token` function.
3. Receive your chosen token ID and add it to the text so far.
4. Use that updated text when asking the model for the next set of scores.

For our example, choosing `191646` extends the text to
`The cat sat on the windowsill`. Gemma then produces new scores for what
comes after that sequence. Choosing a different token changes the context
for later choices. The runner stops when an ending token is selected or the
reply reaches its token limit. It handles these details for you.

The model has already been **trained**: it has learned numerical patterns from
examples of text. Those learned values stay fixed during this exercise. Your
work changes how we select from the scores it produces. A different reply does
not mean you have retrained the model.

### Stage 0: Match tokens with their scores

Open `src/decoders/stage_00_inspect.py`. This supplied warm-up uses the real
Gemma model to explore `The cat sat on the`. You can change the prompt and
see how its tokens and possible continuations change.

#### Explore the provided helpers

We provide three functions in `chat110.support`:

| Function | What it returns |
| --- | --- |
| `tokenize(text)` | A `list[int]` of token IDs for your text, without added beginning or chat markers |
| `token_text(token_id)` | A `str` containing the token's decoded text, including spaces or special markers |
| `next_token_logits(prompt, top_k=10)` | A `dict[int, float]` containing up to ten next-token IDs and their raw logits, highest score first |

For example:

```python
from chat110.support import next_token_logits, token_text, tokenize

prompt: str = "The cat sat on the"
prompt_ids: list[int] = tokenize(prompt)  # [818, 5866, 2838, 580, 506]
print(repr(token_text(5866)))  # ' cat'
logits: dict[int, float] = next_token_logits(prompt, top_k=10)
```

`repr` makes spaces and newline characters visible in the printed output.
The token lookup tells you what an ID represents; `next_token_logits` tells
you which tokens the model favors **after a particular prompt**. It adds
`<bos>` and continues the prompt directly, matching the example above.
It does not apply chat formatting or generate a whole reply.
The `top_k` argument controls how many candidates are returned; it defaults
to `10`.

These helpers load the tokenizer and model as needed and reuse them during
the run. Tokenization and token lookup do not load the model's weights into
memory, though their first use may download the shared model bundle.

#### Match the dictionary's keys and values

Turn the dictionary's keys and values into two lists:

```python
token_ids: list[int] = list(logits.keys())
scores: list[float] = list(logits.values())
```

`logits.keys()` supplies the keys, and `list(...)` puts them into a list.
`logits.values()` supplies the values in the same dictionary insertion order.
For our prompt, the lists begin like this (scores are rounded here):

```text
token_ids: [191646, 1756,   4771,   ...]
scores:    [43.392, 41.113, 39.803, ...]
```

Values at the same position belong together:

| List position | Token ID | Text from `token_text` | Score |
| --- | --- | --- | --- |
| `0` | `191646` | `" windowsill"` | `43.392` |
| `1` | `1756` | `" mat"` | `41.113` |
| `2` | `4771` | `" window"` | `39.803` |

For example, `scores[1]` is about `41.113`, and it belongs to token
`token_ids[1]`, which is `1756`. The position `1`, the ID `1756`, and the score
`41.113` each have a different role. A larger ID does not mean a higher score.
**Keep matching positions connected throughout the exercise.**

In `inspect_logits`, read the supplied loop using `range(len(token_ids))`.
At each position, it prints the position, token ID, decoded text, and score.
The output uses aligned columns and displays logits to three decimal places;
the dictionary keeps the full scores. Remember that list positions start at
zero.

The inspection helper returns the top ten entries in score order to make them
easy to explore. Later, the chat runner passes **all 262,144 entries** to your
`next_token` function in token-ID order. Your decoder must search for the
highest score; it cannot assume the first entry is best. The top ten scores
are still logits. Applying softmax to only this subset would give different
probabilities from applying it to the full vocabulary.

Run the warm-up:

```text
uv run python -m decoders.stage_00_inspect
```

The `-m` tells Python to run a module. Here, `decoders` names the package in `src/` and
`stage_00_inspect` names the Python file without its `.py` extension.

#### Stage 0 checkpoint

Before moving on, confirm that:

- `tokenize(prompt)` returns the five text-token IDs shown above;
- `token_text(5866)` returns `" cat"`, including its leading space;
- the supplied loop visits all ten candidate positions and pairs each ID with
  its text and score;
- you can explain why choosing the largest score would return `191646`, rather
  than position `0` or score `43.392`; and
- changing the prompt changes the next-token scores. Try `The cat ate the`.

### Stage 1: Choose the largest score

Work in `src/decoders/stage_01_greedy.py`.

**Greedy decoding** always chooses the next token that the model considers
most probable, given the text so far. It is called *greedy* because it takes
the best-scoring choice at every step. In this stage, you will work directly
with the model's logit scores.

There is no random draw: given the same prompt, conversation history, and
model calculations, greedy decoding makes the same choices. This gives us
consistent, repeatable behavior that is useful for comparing our programs.
In our example, it always chooses `" windowsill"`, even though `" mat"` and
other continuations also make sense.

In later stages, you will explore a different approach: **stochastic
sampling**, which uses randomness and the model's probabilities to choose
among possible next tokens.

#### Implement `next_token`

Given a nonempty dictionary of token IDs and logits, return the **token ID
with the highest score**. The supplied parallel lists preserve the connection
between IDs and scores. Design a search using loops and conditionals.

Your function must handle negative scores and a dictionary with just one
entry. When several tokens share the highest score, choose the one that
appears first in the dictionary. Preserve the input dictionary and return
an original token ID.

#### Check the small examples

Add calls in your file's `if __name__ == "__main__":` block to check these
cases. Compare your results with the expected token IDs:

| Call | Expected token ID | What it checks |
| --- | --- | --- |
| `next_token({42: 2.0, 7: 1.0, 99: 0.0})` | `42` | The largest score is first |
| `next_token({42: -7.0, 7: -2.0, 99: -2.0})` | `7` | Negative scores and a tie |
| `next_token({99: 4.0, 7: 4.0})` | `99` | The earlier entry wins a tie |
| `next_token({99: -10.0})` | `99` | A single entry |

```text
uv run python -m decoders.stage_01_greedy
```

#### Let your function drive a conversation

Now run:

```text
uv run chat110 --stage 1
```

Type a prompt at `You:`, such as `Give me a short greeting.` The response appears
as it is generated. Your function makes each next-token decision, this time
using the full vocabulary rather than three invented entries.

Keep chatting if you would like. The runner includes previous prompts and
replies in the conversation. Type `/reset` to clear that history or `/quit` to
exit. After changing your code, exit and restart the chat to load your changes.

You can also request one reply and then exit automatically:

```text
uv run chat110 --stage 1 "Give me a short greeting."
```

The quotation marks keep the words together as one prompt. `--stage 1` tells
the runner which file's `next_token` function to use. Replies have a default
limit of 128 tokens, so a reply may end before its sentence is complete.

#### Stage 1 checkpoint

Confirm that:

- your search uses a loop and a conditional;
- negative scores and ties produce the expected IDs;
- your function returns an original dictionary key; and
- you can run a model reply using Stage 1.

An awkward reply does not by itself mean your search is incorrect. Use the
small examples to check the algorithm; use the conversation to observe what
that algorithm does with the model's scores.

Try comparing these questions, starting a fresh conversation for each:

- `What is the most iconic landmark in Chapel Hill?`
- `What is a Python function?`

This small Gemma model fits on your laptop, but its factual knowledge is
limited. You may find that it struggles with local or specialized knowledge,
sometimes making up plausible-sounding details, while giving a useful
starting explanation of a familiar topic such as Python functions. Model
size and training both affect what it can answer reliably. Read both replies
critically: a confident answer can still be wrong, and even a useful answer
may become repetitive. These limitations can appear even when your greedy
decoder is working correctly.

### Stage 2: Turn scores into probabilities

Work in `src/decoders/stage_02_softmax.py`. Build on your Stage 1 solution.

Always taking the largest score gives every other token no chance of being
chosen. Before we can give several tokens a chance, we need a way to describe
how much chance each should have.

A **probability** is a number from `0.0` to `1.0`. For example, `0.25` means a
25% chance. When we choose exactly one item from a list, the probabilities
across the list must add up to `1.0`, representing all the possible choices.

Logits do not satisfy these rules: they can be negative and do not necessarily
add up to one. **Softmax** is a calculation that converts logits into
probabilities while keeping higher-scoring tokens more likely than
lower-scoring tokens.

These are probabilities for choosing the next token. A probability of `0.8`
does not mean a reply has an 80% chance of being factually correct.

#### Understand the softmax calculation

For our scores `[2.0, 1.0, 0.0]`, softmax works as follows. Values in the last
two rows are rounded for display.

| Step | Result | Purpose |
| --- | --- | --- |
| Find the largest score | `2.0` | Establish a shared reference value |
| Subtract it from every score | `[0.0, -1.0, -2.0]` | Keep the next calculation from using very large positive inputs |
| Apply `exp` to each difference | `[1.0, 0.367879, 0.135335]` | Turn the differences into positive relative weights |
| Divide each weight by their total | `[0.665241, 0.244728, 0.090031]` | Make the values add up to one |

The supplied import `from math import exp` makes the `exp` function available.
Algebraically, `exp(x)` means **raise the constant e to the power x**:

$$
\operatorname{exp}(x) = e^x, \qquad e \approx 2.71828
$$

You do not need to derive this constant or the exponential function. Use the
usual rules of exponents to understand these examples:

$$
\begin{aligned}
\operatorname{exp}(0) &= e^0 = 1 \\
\operatorname{exp}(1) &= e^1 \approx 2.71828 \\
\operatorname{exp}(-1) &= e^{-1} = \frac{1}{e} \approx 0.367879 \\
\operatorname{exp}(-2) &= e^{-2} = \frac{1}{e^2} \approx 0.135335
\end{aligned}
$$

In our softmax calculation, `exp(score - largest)` means:

$$
e^{\text{score} - \text{largest}}
$$

Exponentiation gives positive weights even when its inputs are negative,
and a larger input gives a larger result. Dividing each weight by the total
then gives probabilities that sum to one.

Subtracting the largest score keeps the biggest input to `exp` at zero. It
preserves the final probabilities while avoiding numbers too large for the
computer to represent. This is why we follow the same recipe even if the
scores look small enough to use directly.

The results of `exp` are **relative weights**. They describe how much chance
each token should have compared with the others, but their total is not yet
one. The last step, **normalization**, turns them into probabilities.

#### Implement normalization

Start with the simplest building block, `normalize`, so you can check that
it works before using it in a larger operation. Then build `softmax` using
`normalize`, and connect `softmax` to `next_token`.

Write this helper function:

```python
def normalize(weights: list[float]) -> list[float]:
    """Return each weight's share of the total as a new list."""
```

To understand the calculation, imagine weights `[2.0, 3.0, 5.0]`. There are ten
units in total. The first entry has two of those ten units, so its share is
`2.0 / 10.0`, or `0.2`. The other shares are `0.3` and `0.5`.

Return a new list containing each weight's share of the total, in the same
order as the input. Assume weights are nonnegative and at least one is
positive. The input must remain unchanged, zero weights must receive zero
probability, and the result must sum to approximately one.

Use these examples to check your implementation:

```text
normalize([2.0, 3.0, 5.0]) → [0.2, 0.3, 0.5]
normalize([0.0, 4.0])      → [0.0, 1.0]
normalize([3.0, 3.0])      → [0.5, 0.5]
```

**Reflection question:** How is this normalization similar to scaling throttle
in Formula110? What extra requirement must a list of probabilities satisfy
that throttle settings did not?

#### Put the softmax steps together

Write a second helper:

```python
def softmax(scores: list[float]) -> list[float]:
    """Convert scores into next-token probabilities in the same order."""
```

Build `softmax` in these steps, using `[2.0, 1.0, 0.0]` as a running example:

1. **Find the largest score.** Here, it is `2.0`. Keep this value so you can
   subtract the same amount from every score.
2. **Build a new list of weights using `exp`.** Loop through the scores in
   order. For each score, subtract the largest score, pass that difference
   to `exp`, and append the result to your weights list. For the first
   score, `exp(2.0 - 2.0)` gives `1.0`. The remaining calls are
   `exp(1.0 - 2.0)` and `exp(0.0 - 2.0)`, giving approximately `0.367879`
   and `0.135335`. Notice that `exp` takes one number at a time; your loop
   builds the list `[1.0, 0.367879, 0.135335]`.
3. **Normalize the completed weights list and return the probabilities.**
   Call your `normalize` helper with the weights list. It divides each
   weight by their total, approximately `1.503214`, giving
   `[0.665241, 0.244728, 0.090031]`. Return the list that `normalize`
   produces. You can reuse that helper without repeating its calculation
   inside `softmax`.

The numbers above are rounded for display; keep the full values returned by
`exp` in your weights list.

Assume the score list is nonempty and contains finite numbers. Return a new
list in the original order and preserve the input.
Your implementation must work with negative scores, equal scores, and large
scores such as `[1002.0, 1001.0, 1000.0]`.

Update `next_token` to use the probabilities from `softmax` to make a greedy
choice. It must return an original token ID and keep the same tie rule as
Stage 1. This stage does not introduce randomness.

#### Inspect the change

Add checks for `normalize`, `softmax`, and `next_token` in your
`if __name__ == "__main__":` block, then run:

```text
uv run python -m decoders.stage_02_softmax
```

Compare the probabilities with the worked table. Also try equal scores such
as `[-2.0, -2.0]`, which should produce `[0.5, 0.5]`. Try
`[1002.0, 1001.0, 1000.0]`: subtracting the largest value gives the same
differences as our original example, so it should produce the same
probabilities.

Python's `float` values have limited precision. A total such as
`0.9999999999999999` is close enough to one here. Compare the displayed
probabilities to about six decimal places instead of expecting every digit
to match. Very small exponential weights can also round to zero.

Try the same prompt from Stage 1:

```text
uv run chat110 --stage 2 "Give me a short greeting."
```

The next-token choices should be the same as Stage 1. Softmax changes the
numbers but preserves which is largest. It prepares probabilities for the
next stage; it does not make a random choice on its own.

#### Stage 2 checkpoint

Confirm that:

- `normalize` returns a new list whose values add up to approximately one;
- `softmax` subtracts the largest score, applies `exp`, and calls `normalize`;
- all probabilities remain in positions matching their original token IDs;
- equal scores receive equal probabilities, and negative scores work; and
- `next_token` still makes the same greedy choice as Stage 1.

### Finish Part 1

Use your own words to answer these questions:

1. What is the difference between a token ID, a list position, a logit, and a
   probability? Use one of the small examples to explain.
2. Why did Stage 2 keep choosing the same token as Stage 1, even though its
   numbers changed?

You are ready to [create your submission](#create-your-gradescope-submission)
and upload it to the **Part 1** assignment. Stages 3 and 4 can remain
unfinished in this submission. Keep your completed Part 1 functions to reuse
in Part 2.

## Part 2: Sampling and top-p

Build on your completed Part 1 helpers to implement Stages 3 and 4, then
compare the decoding strategies.

### Stage 3: Let probabilities guide a random choice

Work in `src/decoders/stage_03_sampling.py`. Reuse your `normalize` and `softmax`
functions from Stage 2.

**Sampling** means making a random choice according to probabilities. It lets
several continuations remain possible. A token with probability `0.5` should
have more chance of being chosen than one with probability `0.2`.

This does not mean the first token must appear exactly five times in every ten
choices. Probabilities describe chances; small experiments can vary.

#### Divide the space from zero to one

For this example, use probabilities `[0.2, 0.3, 0.5]`. These are convenient
practice values, separate from the softmax example above. Imagine dividing a
one-meter strip into three sections: 20 centimeters, 30 centimeters, and 50
centimeters. A point picked at random along the strip is most likely to land
in the widest section.

We can do the same thing with numbers:

| Position | Probability | Running total | Draws that select this position |
| --- | --- | --- | --- |
| `0` | `0.2` | `0.2` | `0.0 <= draw < 0.2` |
| `1` | `0.3` | `0.5` | `0.2 <= draw < 0.5` |
| `2` | `0.5` | `1.0` | `0.5 <= draw < 1.0` |

A **draw** is the random number used for one choice. A draw of `0.4` falls
in the second section, which spans `0.2` up to `0.5`, so it selects position
`1`.

The running total marks the end of each section. Adding the next probability
extends that end by exactly the width that token should receive.

#### Implement `sample_index`

Write:

```python
def sample_index(probabilities: list[float], draw: float) -> int:
    """Return the position selected by a draw from zero up to, but not including, one."""
```

Given a nonempty probability list and a draw between zero (included) and one
(excluded), return the position whose probability interval contains the draw.
The intervals follow the original list order, and each interval's width is
its probability. Preserve the input list. This function uses the supplied
draw; it does not generate a random number itself.

This helper returns a **list position**, not a token ID. It does not receive
the token IDs, so looking up the selected ID is still `next_token`'s job.

Add calls with fixed draws to your `if __name__ == "__main__":` block so you
can check the calculation without depending on chance:

| Call | Expected position |
| --- | --- |
| `sample_index([0.2, 0.3, 0.5], 0.0)` | `0` |
| `sample_index([0.2, 0.3, 0.5], 0.2)` | `1` |
| `sample_index([0.2, 0.3, 0.5], 0.4)` | `1` |
| `sample_index([0.2, 0.3, 0.5], 0.5)` | `2` |
| `sample_index([0.2, 0.3, 0.5], 0.999)` | `2` |
| `sample_index([0.0, 1.0, 0.0], 0.0)` | `1` |

At a shared boundary, the draw belongs to the interval that begins there.
For example, a draw of `0.2` selects position `1` in the table. An entry with
zero probability has no width and must never be selected, even when the draw
is zero.

There is one rounding detail to handle. The probabilities may total slightly
less than one. If a valid draw falls beyond that total because of rounding,
the required result is the last position with a positive probability. Trailing
zero-probability entries must still be excluded.

#### Connect the sampler to `next_token`

The supplied `random` function returns a number greater than or equal to
`0.0` and strictly less than `1.0`. Equal-sized sections of our number strip
have equal chances of receiving its draw. The different widths assigned to
tokens are what make some tokens more likely than others.

Update `next_token` to sample according to the probabilities from `softmax`,
using your `sample_index` helper. Each call must use exactly one fresh draw
from the supplied `random()` function and return an original token ID.

Add a check of `next_token` alongside your fixed-draw examples, then run your
checks and try a real reply:

```text
uv run python -m decoders.stage_03_sampling
uv run chat110 --stage 3 --seed 110 "Give me a short greeting."
```

A **seed** sets the starting point for Python's sequence of random numbers.
Restarting with the same seed lets you repeat that sequence when comparing
programs in the same environment. The runner sets it once at startup. Do not
reset the seed inside `next_token`: doing so would restart the sequence at
every token instead of taking a new draw from it.

Try seeds `110`, `111`, and `112`, keeping the prompt fixed. Some replies may
match; a random choice can select the same token more than once.

#### Stage 3 checkpoint

Confirm that:

- the fixed draws in the table select the expected positions;
- zero-probability entries cannot be selected;
- your function handles a running total just short of one;
- `next_token` uses softmax, makes one draw, and returns the selected token ID;
  and
- you can explain why selecting a list position with equal chance would ignore
  the model's probabilities.

### Stage 4: Limit the candidates with top-p

Work in `src/decoders/stage_04_top_p.py`. Keep your normalization, softmax, and
sampling functions from Stage 3, along with this file's supplied imports and
`TOP_P` setting.

Stage 3 gives even very unlikely tokens a chance when their probabilities are
greater than zero. This adds variety, but sampling unlikely continuations can
also take a reply off track or introduce made-up details. False or unsupported
claims presented as facts are often called **hallucinations**. We want to
keep some variety while limiting these less likely continuations.

**Top-p** keeps the most likely tokens until their combined probability reaches
a threshold named `p`. That combined probability is sometimes called
**probability mass**; here it simply means the sum of the included probabilities.

Keeping the choice among the model's more likely continuations can make
responses more coherent. However, top-p does not check facts or eliminate
hallucinations: the model can assign a high probability to an incorrect
answer. A smaller `p` narrows the choices, but does not guarantee greater
factual accuracy.

For example, `p = 0.75` means to keep the leading candidates that together
account for at least 75% of the original probability. It does not mean to keep
75% of the tokens.

#### Follow a small example

This time, use four fictional tokens in the following original order:

| Position | Token ID | Probability |
| --- | --- | --- |
| `0` | `42` | `0.125` |
| `1` | `7` | `0.5` |
| `2` | `99` | `0.125` |
| `3` | `501` | `0.25` |

We provide `rank_indices(probabilities)` in `src/chat110/support.py`. For this list, it
returns `[1, 3, 0, 2]`: the original positions ordered from largest probability
to smallest. Tied probabilities keep their original order. You do not need to
implement sorting.

With `p = 0.75`, the two leading candidates are at positions `1` and `3`.
Their probabilities, `0.5` and `0.25`, total `0.75`. Neither candidate alone
accounts for enough probability, so both are retained.

Include the token that reaches **or crosses** the threshold. For example, if
`p` were `0.7`, we would still keep both tokens. Tokens are whole choices;
we do not keep part of the second token to reach exactly `0.7`.

The kept values, in their original positions, are:

```text
[0.0, 0.5, 0.0, 0.25]
```

Zeros make the other tokens ineligible. Keeping their positions in the list
preserves the connection to `token_ids`.

#### Why normalize again?

The kept probabilities now total `0.75`. Our sampler needs a total of one
because its random draws can fall anywhere from zero up to one. Leaving the
total at `0.75` would leave some draws outside all the intended sections.

Use your existing `normalize` function to divide the kept values by `0.75`:

```text
[0.0, 0.666667, 0.0, 0.333333]  # approximately
```

The two retained tokens now have about a two-thirds and a one-third chance.
The first is still twice as likely as the second. Top-p removes candidates;
normalization redistributes their probability proportionally among those
remaining. It does not give the remaining tokens equal chances.

#### Implement `top_p`

Write:

```python
def top_p(probabilities: list[float], p: float) -> list[float]:
    """Keep the leading candidates reaching p and return new probabilities."""
```

Given a nonempty probability list and a threshold `0.0 < p <= 1.0`, return a
new probability list restricted to the smallest leading group in ranked
order whose combined probability reaches or exceeds `p`. Use the supplied
`rank_indices` helper and your `normalize` function.

Your result must satisfy these requirements:

- Include the candidate that reaches or crosses the threshold, keeping at
  least one candidate.
- Preserve the original length and positions. Excluded candidates receive
  zero probability; retained candidates keep their relative proportions and
  together receive a total probability of approximately one.
- For `p = 1.0`, return an unchanged copy of the probabilities.
- Preserve the input list and use the ranking helper's order to resolve ties.

Update `next_token` to sample from the softmax probabilities after top-p
filtering. Use `TOP_P` as the threshold and reuse your `sample_index` helper.
Each call must make exactly one fresh random draw and return an original
token ID. The runner sets `TOP_P` from the `--top-p` option; it defaults to
`0.9`.

#### Try different thresholds

Add checks for `top_p` and `next_token` to your `if __name__ == "__main__":`
block. Run your file to inspect the results:

```text
uv run python -m decoders.stage_04_top_p
```

For `[0.125, 0.5, 0.125, 0.25]`, check that `p = 0.75` gives the worked result,
`p = 0.1` keeps only position `1`, and `p = 1.0` preserves all four probabilities.
Also try `p = 0.8`: which additional position must be kept to cross the threshold?

Then compare two model runs:

```text
uv run chat110 --stage 4 --top-p 0.5 --seed 110 "Give me a short greeting."
uv run chat110 --stage 4 --top-p 0.9 --seed 110 "Give me a short greeting."
```

The smaller threshold keeps fewer or the same number of candidates for any
given probability list. But the number kept can change at each token decision:
one very likely token might reach the threshold alone, while several similarly
likely tokens might be needed at another point in the reply.

#### Stage 4 checkpoint

Confirm that:

- your filter includes the candidate that reaches or crosses the threshold;
- a small positive `p` still keeps at least one candidate;
- `p = 1.0` returns an unfiltered copy;
- excluded entries are zero, and retained entries are normalized again;
- all entries keep their original positions; and
- `next_token` samples from the filtered probabilities and returns an original
  token ID.

### Compare your decoding strategies

Choose one prompt and compare Stages 1, 3, and 4. For example:

```text
Write two sentences about a robot learning to cook.
```

Use the same prompt and begin a fresh conversation for each run. The quoted
prompt form of the command does this automatically; in interactive chat, use
`/reset`. Keep the model and reply limit the same. Otherwise, you might mistake
a change in conversation history or reply length for a change in your algorithm.

For Stages 3 and 4, try the same few seeds, such as `110`, `111`, and `112`.
When comparing top-p thresholds, change only the threshold for each pair of
runs. A seed helps make the comparison repeatable on your machine; exact
sentences need not match a classmate's computer.

Look for repeated wording, variation, and whether the reply stays connected
to the prompt. Several runs give you more to compare than one lucky or
unlucky reply. A different choice is not automatically a better choice.

### Finish Part 2

Use your own words to answer these questions:

1. In Stage 3, how does a larger probability give a token more chance of being
   chosen? What does the running total represent?
2. In Stage 4, why do we normalize again after removing candidates? Why would
   choosing equally among the remaining tokens give a different result?
3. How can the same `p` keep one token at one point in a reply and several at
   another?
4. What changed in your experiments, and what stayed fixed? Support one
   observation with examples from your runs.

Your final decoder combines small, familiar operations. The model supplies
scores; softmax turns them into probabilities; top-p limits the available
choices; sampling selects a position; and a list lookup recovers the token ID.
The runner repeats that one-token decision to build the text you see.

Regenerate your submission ZIP with your completed Stages 3 and 4, then
upload it to the **Part 2** assignment.

## Create your Gradescope submission

Use this same process for either part:

1. In VS Code, select **Terminal > Run Task**.
2. Select **Create Chat110 Submission** for the `chat110` folder.
3. Wait for the terminal to print the completed ZIP's path.

You can also run the same exporter from a terminal in the project root:

```text
uv run python scripts/export_chat110_exercise.py
```

Upload the timestamped `yy.mm.dd-hh.mm.ss-chat110-exercise.zip` from the
project root to the Gradescope assignment for the part you are submitting.
This ZIP contains all your `decoders` Python files and a submission manifest.
The same bundle is accepted by both assignments: Part 1 grades only Stages
1 and 2, and Part 2 grades only Stages 3 and 4. You do not need to remove
unfinished stages for Part 1. Regenerate the ZIP after editing your code.
Submit the generated ZIP rather than the entire project,
the model cache, or the provided `chat110` runtime.

Each part is worth **100 base points**, with **50 points** for each of its two
graded stages. Stage 0 is a supplied warm-up with a zero-point presence/syntax
check in Part 1; its absence does not deduct points from Stages 1 and 2.
Each graded stage includes **4 points** for a module docstring, your nine-digit
`__author__` PID, the supplied typed function signatures and their docstrings,
and type annotations on every function's parameters and return value. The
remaining **46 points** check that stage's functions with small deterministic
examples. Later stages check their copies
of earlier helpers too, so preserve those implementations. Function names and
types are required; parameter names may differ.

Helpers earn credit separately from `next_token`, but each check group awards
its points only when all its cases pass. The feedback shows points by stage,
the base score, early-submission bonus, and final score.

Grading checks negative logits and ties, normalization, large logits, exact
sampling boundaries, zero probabilities, and top-p thresholds. Keep the first
entry on a tie, preserve inputs, and return new lists from the list-producing
helpers. Use the supplied `random()` import for exactly one fresh draw in each
sampled `next_token` call; never call `seed` inside your functions. The provided
`rank_indices` helper is available in the autograder. No model download or
quality judgment of generated prose is involved, and there is no leaderboard.

Following the course convention, submitting at least 48 hours early adds 5
points; at least 24 hours early adds 3 points. Each part's bonus is based on
Gradescope's recorded submission time and that part's assignment deadline.
These are alternative bonuses, not cumulative. A complete submission can earn
105 points with the 48-hour bonus or 103 points with the 24-hour bonus in each
part. Read the separate feedback for each stage and resubmit to the
corresponding assignment as needed.
