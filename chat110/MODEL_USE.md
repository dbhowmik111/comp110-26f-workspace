# Model-use agreement and attribution

This academic application uses **Gemma 3 270M IT**, developed by **Google
DeepMind**. The model comes from `google/gemma-3-270m-it`, revision
`ac82b4e820549b854eebf28ce6dedaf9fdfa17b3`. The upstream model weights,
tokenizer, chat template, and configuration files are packaged without
modification. Converting weights to float32 in memory at inference time does
not change the redistributed files.

## Terms governing the model

Downloading, using, reproducing, modifying, or distributing this model is
subject to the [Gemma Terms of Use](licenses/GEMMA_TERMS_OF_USE.md), including
the use restrictions in Section 3.2. Those terms and the
[Gemma Prohibited Use Policy](licenses/GEMMA_PROHIBITED_USE_POLICY.md) are
incorporated into this model-use agreement by reference. By using the model,
you agree to those terms. You must not use the model or its derivatives for
uses prohibited by that policy or in violation of applicable laws and
regulations, and you must not allow others to do so. These are conditions of
your permission to use and redistribute the model, including in this
academic application.

If you redistribute the model or derivatives, you must pass on the full
Gemma Terms of Use, the required NOTICE, and these use restrictions in the
agreement governing your redistribution. Prominently identify any files you
modify. Preserve the Google attribution and the model's provenance.

The model remains subject to Google's terms independently of any license for
this application's Python code. Academic use does not remove these
obligations. The included terms contain Google's warranty disclaimer and
limitation of liability. Outputs can be inaccurate or inappropriate; users
are responsible for reviewing and using them.

## Source documents

- [Google's Gemma Terms of Use](https://ai.google.dev/gemma/terms), last
  modified April 1, 2026; local copy in `licenses/GEMMA_TERMS_OF_USE.md`.
- [Google's Gemma Prohibited Use Policy](https://ai.google.dev/gemma/prohibited_use_policy),
  last modified February 21, 2024; local copy in
  `licenses/GEMMA_PROHIBITED_USE_POLICY.md`.
- [Original model repository and pinned revision](https://huggingface.co/google/gemma-3-270m-it/tree/ac82b4e820549b854eebf28ce6dedaf9fdfa17b3).
- `MODEL_CARD.md` is an unchanged copy of Google's model card at that revision.

The legal texts were retrieved from Google on November 8, 2026. Only their
HTML presentation was converted to Markdown, with links made absolute; the
terms and policy wording were preserved. The additional academic attribution
and provenance statements in this repository are separate from Google's terms.

## Academic citation

Google's model card supplies this citation for Gemma 3:

```bibtex
@article{gemma_2025,
    title={Gemma 3},
    url={https://arxiv.org/abs/2503.19786},
    publisher={Google DeepMind},
    author={Gemma Team},
    year={2025}
}
```

Google does not sponsor or endorse this academic application. No rights to
Google's logos or trademarks are granted by the Gemma terms.
