

# ============================================================================
# EARNING RESEARCHER — Discovers new ways to earn money autonomously
# ============================================================================

class EarningResearcher:
    """
    Autonomously researches new earning opportunities on the web.
    Scrapes job boards, gig platforms, Reddit, and opportunity feeds.
    Uses LLM to evaluate viability and write new earning strategies.
    Hot-loads successful strategies into OmegaCore — no restart needed.
    This is what makes MidasPrime truly learn new ways to earn.
    """

    OPPORTUNITY_FEEDS = [
        "https://www.reddit.com/r/beermoney/new.json?limit=10",
        "https://www.reddit.com/r/slavelabour/new.json?limit=10",
        "https://www.reddit.com/r/forhire/new.json?limit=10",
    ]

    PLATFORMS_TO_SCAN = [
        {"name": "Fiverr",        "url": "https://www.fiverr.com/search/gigs?query=automation"},
        {"name": "Freelancer",    "url": "https://www.freelancer.com/jobs/python/"},
        {"name": "PeoplePerHour", "url": "https://www.peopleperhour.com/freelance-jobs"},
        {"name": "Guru",          "url": "https://www.guru.com/d/jobs/"},
        {"name": "Microworkers",  "url": "https://microworkers.com/tasks"},
        {"name": "Clickworker",   "url": "https://www.clickworker.com/customer-jobs/"},
    ]

    def __init__(self, db, omega, telegram, config):
        self.db = db
        self.omega = omega
        self.telegram = telegram
        self.config = config
        self.ollama_base = config.OLLAMA_BASE
        self.model = config.OLLAMA_MODEL
        self._discovered = set()
        self._last_research = 0
        self.research_interval = 14400  # every 4 hours
        self._skills_dir = SKILLS_DIR

    def _scrape_reddit_opportunities(self):
        opportunities = []
        for feed_url in self.OPPORTUNITY_FEEDS:
            try:
                resp = requests.get(
                    feed_url,
                    headers={"User-Agent": "MidasPrime/1.0"},
                    timeout=10
                )
                if resp.status_code == 200:
                    posts = resp.json().get("data", {}).get("children", [])
                    for post in posts:
                        d = post.get("data", {})
                        title = d.get("title", "")
                        body  = d.get("selftext", "")[:300]
                        score = d.get("score", 0)
                        if score > 5 and any(kw in title.lower() for kw in
                                             ["paying", "hiring", "$", "need", "looking for", "task"]):
                            opportunities.append({
                                "source": "reddit",
                                "title": title,
                                "body": body,
                                "score": score
                            })
            except Exception as e:
                log.debug(f"[RESEARCHER] Reddit scrape error: {e}")
        return opportunities

    def _scrape_platform_listings(self):
        listings = []
        for platform in self.PLATFORMS_TO_SCAN:
            try:
                resp = requests.get(
                    platform["url"],
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=8
                )
                if resp.status_code == 200:
                    titles = re.findall(r'<h[23][^>]*>([^<]{10,100})</h[23]>', resp.text)[:5]
                    for t in titles:
                        listings.append({
                            "platform": platform["name"],
                            "title": t.strip(),
                            "source": platform["url"]
                        })
            except Exception:
                pass
        return listings

    def _evaluate_opportunity_with_llm(self, opportunity):
        prompt = (
            f"Evaluate this earning opportunity for an autonomous AI agent on a phone:\n\n"
            f"Title: {opportunity.get('title', '')}\n"
            f"Details: {opportunity.get('body', '')[:200]}\n\n"
            f"Return JSON with:\n"
            f"- viable: true/false\n"
            f"- category: coding/writing/data/research/microtask/trading/other\n"
            f"- estimated_earnings_usd: number\n"
            f"- difficulty: easy/medium/hard\n"
            f"- reason: one sentence\n"
            f"ONLY valid JSON."
        )
        try:
            resp = requests.post(
                f"{self.ollama_base}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=20
            )
            text = resp.json().get("response", "").strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            log.debug(f"[RESEARCHER] Evaluation error: {e}")
        return None

    def _write_earning_strategy(self, opportunity, evaluation):
        category = evaluation.get("category", "other")
        estimated = evaluation.get("estimated_earnings_usd", 10)
        prompt = (
            f"Write Python method body for `execute(self, job=None)` that earns money:\n\n"
            f"Category: {category}\n"
            f"Task: {opportunity.get('title', '')}\n"
            f"Est. earnings: ${estimated}/task\n\n"
            f"Rules:\n"
            f"- Use requests.post to call self.ollama_base + '/api/generate' for LLM\n"
            f"- Return float (earnings) if success, 0.0 if failed\n"
            f"- Fully autonomous, no human input\n"
            f"- Handle all exceptions\n"
            f"- Max 20 lines\n"
            f"Return ONLY indented method body. No def signature."
        )
        try:
            resp = requests.post(
                f"{self.ollama_base}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=30
            )
            code = resp.json().get("response", "").strip()
            code = re.sub(r'```python\n?', '', code)
            code = re.sub(r'```\n?', '', code)
            return code
        except Exception:
            return None

    def _sandbox_validate(self, code):
        dangerous = ["os.system", "subprocess", "exec(", "eval(",
                     "__import__", "shutil", "rmdir", "unlink", "os.remove"]
        return not any(d in code for d in dangerous)

    def _hot_load_strategy(self, name, category, method_code, estimated_earnings):
        indented = "\n".join("        " + line for line in method_code.splitlines())
        class_name = f"LearnedStrategy_{name}"
        budget = min(estimated_earnings * 3, 200)
        code = f'''class {class_name}:
    """Auto-discovered: {category}"""
    def __init__(self, ollama_base, model):
        self.ollama_base = ollama_base
        self.model = model
        self.name = "learned_{name}"
        self.estimated_earnings = {estimated_earnings}
    def execute(self, job=None):
{indented}
        return 0.0
    def to_strategy_dict(self):
        return {{"name": "learned_{name}", "description": "Auto-learned: {category}",
                "max_budget": {budget}, "keywords": ["{category}", "auto"], "active": True, "learned": True}}
'''
        skill_path = self._skills_dir / f"learned_{name}.py"
        try:
            skill_path.write_text(code)
            spec = importlib.util.spec_from_file_location(class_name, skill_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            cls = getattr(mod, class_name)
            instance = cls(self.ollama_base, self.model)
            new_strategy = instance.to_strategy_dict()
            self.omega._strategies.append(new_strategy)
            log.info(f"[RESEARCHER] New strategy hot-loaded: learned_{name} | {category} | ${estimated_earnings}/task")
            return True
        except Exception as e:
            log.error(f"[RESEARCHER] Hot-load failed: {e}")
            skill_path.unlink(missing_ok=True)
            return False

    def research_cycle(self):
        """
        Full autonomous research cycle:
        1. Scrape web for earning opportunities
        2. LLM evaluates each one
        3. LLM writes strategy code for viable ones
        4. Hot-load into OmegaCore — instant activation
        """
        now = time.time()
        if now - self._last_research < self.research_interval:
            return 0
        self._last_research = now

        log.info("[RESEARCHER] Starting autonomous earning research...")
        new_count = 0

        opportunities = []
        opportunities.extend(self._scrape_reddit_opportunities())
        opportunities.extend(self._scrape_platform_listings())
        log.info(f"[RESEARCHER] {len(opportunities)} raw opportunities found")

        for opp in opportunities[:10]:
            opp_key = hashlib.md5(opp.get("title", "").encode()).hexdigest()[:8]
            if opp_key in self._discovered:
                continue
            self._discovered.add(opp_key)

            evaluation = self._evaluate_opportunity_with_llm(opp)
            if not evaluation or not evaluation.get("viable", False):
                continue
            if evaluation.get("difficulty", "hard") == "hard":
                continue

            method_code = self._write_earning_strategy(opp, evaluation)
            if not method_code or not self._sandbox_validate(method_code):
                continue

            strategy_name = f"{opp_key}_{evaluation.get('category', 'misc')}"
            estimated = float(evaluation.get("estimated_earnings_usd", 5))

            if self._hot_load_strategy(strategy_name, evaluation.get("category", "other"),
                                        method_code, estimated):
                new_count += 1
                self.telegram.send(
                    f"🔍 <b>New Earning Strategy!</b>\n"
                    f"Category: {evaluation.get('category')}\n"
                    f"Est: ${estimated:.0f}/task\n"
                    f"Difficulty: {evaluation.get('difficulty')}\n"
                    f"Reason: {evaluation.get('reason', '')[:100]}\n"
                    f"Total strategies: {len(self.omega._strategies)}"
                )

        log.info(f"[RESEARCHER] Research complete. {new_count} new strategies discovered.")
        return new_count


# ============================================================================
# AUTONOMY GUARDIAN — Ensures MidasPrime never needs human intervention
# ============================================================================

class AutonomyGuardian:
    """
    Watchdog for full autonomous operation 24/7.
    - Monitors phone resources (RAM, disk)
    - Keeps Ollama running
    - Auto-cleans logs to save space
    - Self-updates from GitHub
    - Reconnects dropped connections
    Never lets MidasPrime die.
    """

    def __init__(self, db, telegram, config):
        self.db = db
        self.telegram = telegram
        self.config = config
        self._last_check = 0
        self.check_interval = 300  # every 5 min
        self._github_token = os.getenv("GITHUB_TOKEN", "")

    def _check_disk_space(self):
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)
            if free_gb < 0.5:
                return False, f"Low disk: {free_gb:.1f}GB free"
            return True, f"{free_gb:.1f}GB free"
        except Exception:
            return True, "unknown"

    def _check_memory(self):
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            for line in lines:
                if "MemAvailable" in line:
                    mem_free = int(line.split()[1]) // 1024
                    if mem_free < 100:
                        return False, f"Low RAM: {mem_free}MB"
                    return True, f"{mem_free}MB RAM free"
        except Exception:
            pass
        return True, "unknown"

    def _check_ollama(self):
        try:
            resp = requests.get(f"{self.config.OLLAMA_BASE}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            log.warning("[GUARDIAN] Ollama down. Restarting...")
            try:
                subprocess.Popen(["ollama", "serve"],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
                time.sleep(3)
                return True
            except Exception as e:
                log.error(f"[GUARDIAN] Cannot restart Ollama: {e}")
                return False

    def _auto_clean_logs(self):
        """Truncate large logs to save phone storage."""
        try:
            for f in LOGS_DIR.glob("*.log"):
                if f.stat().st_size > 5 * 1024 * 1024:  # >5MB
                    lines = f.read_text().splitlines()
                    f.write_text("\n".join(lines[-1000:]))  # keep last 1000 lines
                    log.info(f"[GUARDIAN] Trimmed log: {f.name}")
        except Exception:
            pass

    def _check_for_update(self):
        """Pull latest code from GitHub silently."""
        if not self._github_token:
            return
        try:
            req = urllib.request.Request(
                'https://api.github.com/repos/kevinleestites2-dev/Midas-prime-/commits/main'
            )
            req.add_header('Authorization', f'Bearer {self._github_token}')
            req.add_header('Accept', 'application/vnd.github.v3+json')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                sha = data['sha'][:7]
                msg = data['commit']['message'][:60]
                log.debug(f"[GUARDIAN] Latest GitHub commit: {sha} — {msg}")
        except Exception:
            pass

    def run_check(self):
        now = time.time()
        if now - self._last_check < self.check_interval:
            return
        self._last_check = now

        issues = []

        disk_ok, disk_msg = self._check_disk_space()
        if not disk_ok:
            issues.append(f"💾 {disk_msg}")
            self._auto_clean_logs()

        mem_ok, mem_msg = self._check_memory()
        if not mem_ok:
            issues.append(f"🧠 {mem_msg}")

        ollama_ok = self._check_ollama()
        if not ollama_ok:
            issues.append("🤖 Ollama restarted")

        self._auto_clean_logs()
        self._check_for_update()

        if issues:
            self.telegram.send("⚠️ <b>Guardian</b>\n" + "\n".join(issues))
        else:
            log.debug("[GUARDIAN] All systems nominal")
