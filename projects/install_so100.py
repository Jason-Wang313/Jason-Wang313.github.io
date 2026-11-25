"""Install project extensions in a disposable copy of the pinned ETH HW3 tree."""
import argparse
from pathlib import Path


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Unexpected course template around {old!r}")
    return text.replace(old, new, 1)


def install(target, epochs):
    here = Path(__file__).resolve().parent
    train = target / "scripts/train.py"
    model = target / "hw3/model.py"
    source = train.read_text(encoding="utf-8")
    source = replace_once(source, "from hw3.model import BasePolicy, build_policy",
        "from hw3.model import ObstaclePolicy as BasePolicy, build_policy")
    source = replace_once(source, 'choices=["obstacle", "multitask"]',
        'choices=["obstacle", "diffusion"]')
    for key, value in (("EPOCHS", str(epochs)), ("BATCH_SIZE", "64"), ("LR", "3e-4")):
        source = replace_once(source, key + " = ...", key + " = " + value)
    source = replace_once(source,
        "        # TODO: Implement the training step for one batch here.\n"
        "        # This mostly: Get states and action_chunks onto the correct device, compute the loss, and step the optimizer.",
        "        optimizer.zero_grad(set_to_none=True)\n"
        "        loss = model.compute_loss(states.to(device), action_chunks.to(device))\n"
        "        loss.backward()\n        optimizer.step()\n"
        "        total_loss += loss.item()\n        n_batches += 1")
    source = replace_once(source, "        # TODO: Implement the evaluation step for one batch here.",
        "        total_loss += model.compute_loss(states.to(device), action_chunks.to(device)).item()\n"
        "        n_batches += 1")
    source = replace_once(source, "        # TODO: build with your desired specifications",
        "        chunk_size=args.chunk_size,")
    source = replace_once(source, "    # optimizer =\n    # scheduler =",
        "    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)\n"
        "    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)")
    if ".train.before-portfolio.py" in {p.name for p in train.parent.iterdir()}:
        raise ValueError("Use a fresh course copy.")
    train.with_name(".train.before-portfolio.py").write_bytes(train.read_bytes())
    model.with_name(".model.before-portfolio.py").write_bytes(model.read_bytes())
    (model.parent / "portfolio_diffusion.py").write_bytes((here / "diffusion.py").read_bytes())
    model.write_bytes((here / "so100_policy.py").read_bytes())
    train.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hw3", type=Path)
    parser.add_argument("--epochs", type=int, default=25)
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("--epochs must be positive")
    install(args.hw3, args.epochs)
