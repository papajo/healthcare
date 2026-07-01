 Below is a complete, step‑by‑step playbook for pulling the Agency‑Agents skill set into any of your own project workspaces – whether you are coding locally on your laptop, inside a Docker        
 container, or inside CI/CD.                                                                                                                                                                        
 The instructions cover:                                                                                                                                                                            
                                                                                                                                                                                                    
 ┌───────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────┐                                        
 │ What you want to do                               │ Where you do it                                                                                     │                                        
 ├───────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤                                        
 │ Make the skill files visible to the Pi runtime    │ Set the PI_SKILLS_PATH env‑var or edit the Pi config file.                                          │                                        
 ├───────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤                                        
 │ Install the skills into a specific workspace      │ Run ../scripts/install.sh from that workspace (or give it the path to the skill repo).              │                                        
 ├───────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤                                        
 │ Invoke a skill from the command line              │ pi <skill‑name> … (or pi run <skill‑slug>).                                                         │                                        
 ├───────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤                                        
 │ Call a skill from VS Code                         │ Add the skill‑path to settings.json, then use the “Agency‑Agents: Run Skill” command palette entry. │                                        
 ├───────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────┤                                        
 │ Do it inside Docker / CI without a global install │ Bind‑mount the skill repo into the container and point PI_SKILLS_PATH at that mount.                │                                        
 └───────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────┘                                        
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 1️⃣  What “invoking a skill” actually means                                                                                                                                                         
                                                                                                                                                                                                    
 - In the Agency‑Agents ecosystem a skill lives as a single markdown file (SKILL.md) plus any ancillary assets (scripts, tests, templates).                                                         
 - The Pi runtime loads a skill by name (agency-<slug>) from any directory listed in PI_SKILLS_PATH.                                                                                                
 - Once loaded the runtime can:                                                                                                                                                                     
     - Execute the script named in script: (or the default install.sh/convert.sh depending on the skill type).                                                                                      
     - Render its documentation for you to read.                                                                                                                                                    
     - Expose any helpers it provides as a CLI command (pi <slug> …) that you can call from any shell.                                                                                              
                                                                                                                                                                                                    
 So “invoking” = “tell the Pi runtime to run the entrypoint script of a particular skill”—and you can do that from any working directory, as long as the runtime knows where to find the skill      
 files.                                                                                                                                                                                             
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 2️⃣  Prepare a workspace that can see the skills                                                                                                                                                    
                                                                                                                                                                                                    
 ### 2.1 Choose (or create) a project folder                                                                                                                                                        
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   mkdir -p ~/my-project/healthcare-ops                                                                                                                                                             
   cd ~/my-project/healthcare-ops                                                                                                                                                                   
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 │ Why keep the skills outside the project?                                                                                                                                                         
 │ Skills are shared across many projects. Storing them once under ~/pi-skills/agency-agents (or wherever you clone the repo) prevents duplication and gives you a single source of truth.          
                                                                                                                                                                                                    
 ### 2️⃣  Tell Pi where to look                                                                                                                                                                      
                                                                                                                                                                                                    
 You have three equivalent ways to point Pi at the skill repo. Pick whichever fits your workflow.                                                                                                   
                                                                                                                                                                                                    
 #### A️⃣                                                                                                                                                                                             #### A️⃣  Global environment variable                                                                                                                                                                #### A️⃣  Global environment variable (recommended                                                                                                                                                   #### A️⃣  Global environment variable (recommended for personal machines)                                                                                                                            ⠋ Working...                                                                                                                                                                                       
                                                                                                                                                                                                    
 Add this to ~/.bashrc, ~/.zshrc, or ~/.profile (pick the shell you use):                                                                                                                           
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   export PI_SKILLS_PATH="${HOME}/pi-skills/agency-agents:${PI_SKILLS_PATH:-}"                                                                                                                      
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 Then reload:                                                                                                                                                                                       
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   source ~/.bashrc   # or ~/.zshrc                                                                                                                                                                 
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 │ Check it worked                                                                                                                                                                                  
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   echo $PI_SKILLS_PATH                                                                                                                                                                             
   # → /home/you/pi-skills/agency-agents:/home/you/.pi/skills   (etc.)                                                                                                                              
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 #### B️⃣  Project‑local pi.config.json                                                                                                                                                               
                                                                                                                                                                                                    
 Create a file called pi.config.json at the root of your project:                                                                                                                                   
                                                                                                                                                                                                    
 ```json                                                                                                                                                                                            
   {                                                                                                                                                                                                
     "skills": {                                                                                                                                                                                    
       "path": [                                                                                                                                                                                    
         "/home/you/pi-skills/agency-agents"                                                                                                                                                        
       ]                                                                                                                                                                                            
     }                                                                                                                                                                                              
   }                                                                                                                                                                                                
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 The Pi VS Code extension automatically reads this file if it lives in the workspace folder.                                                                                                        
                                                                                                                                                                                                    
 #### C️⃣                                                                                                                                                                                             #### C️⃣  Directly in VS                                                                                                                                                                             #### C️⃣  Directly in VS Code settings                                                                                                                                                               #### C️⃣  Directly in VS Code settings (per‑workspace)                                                                                                                                               
                                                                                                                                                                                                    
 Open Command Palette → Preferences: Open Settings (JSON), then add:                                                                                                                                
                                                                                                                                                                                                    
 ```json                                                                                                                                                                                            
   {                                                                                                                                                                                                
     "pi.skills.path": [                                                                                                                                                                            
       "/home/you/pi-skills/agency-agents"                                                                                                                                                          
     ]                                                                                                                                                                                              
   }                                                                                                                                                                                                
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 │ Note – The key is "pi.skills.path" (note the dot before skills). The value is an array of strings (you can list multiple roots if you like).                                                     
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 3️⃣  Install the specific skills you need inside that workspace                                                                                                                                     
                                                                                                                                                                                                    
 From the project root (the folder you just created), run the install script once:                                                                                                                  
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # Assuming you still have the Agency‑Agents repo cloned at ~/pi-skills/agency-agents                                                                                                             
   ../scripts/install.sh --tool claude-code --division healthcare                                                                                                                                   
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 What the command does:                                                                                                                                                                             
                                                                                                                                                                                                    
 1. Copies the relevant markdown skill files (*.md) into ~/.claude/agents/ (or the platform‑specific folder).                                                                                       
 2. Generates any necessary runtime assets (e.g., the SKILL.md wrapper for Antigravity).                                                                                                            
 3. Registers the skill with the Pi runtime using the path you set in PI_SKILLS_PATH.                                                                                                               
                                                                                                                                                                                                    
 │ Tip: If you only need a single skill (e.g., agency-healthcare-architect), you can be even more surgical:                                                                                         
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   ./scripts/install.sh --tool claude-code --agent agency-healthcare-architect                                                                                                                      
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 All installed skills become instantly addressable via the Pi CLI:                                                                                                                                  
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   pi agency-healthcare-architect --help                                                                                                                                                            
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 4️⃣  Invoke a skill from the command line (anywhere)                                                                                                                                                
                                                                                                                                                                                                    
 Because PI_SKILLS_PATH is on your $PATH, you can call any installed skill from any directory:                                                                                                      
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # Example: Run the “Healthcare Architect” skill to generate a skeleton system design                                                                                                             
   pi agency-healthcare-architect --input "design a price‑cap engine for emergency care"                                                                                                            
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 The exact CLI signature depends on the skill, but the pattern is always:                                                                                                                           
                                                                                                                                                                                                    
 ```                                                                                                                                                                                                
   pi <skill‑slug> [options] [arguments]                                                                                                                                                            
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 If you ever forget which skills are available in the current workspace, run:                                                                                                                       
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   pi --list-skills                                                                                                                                                                                 
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 5️⃣  Invoke a skill from VS Code (the graphical way)                                                                                                                                                
                                                                                                                                                                                                    
 1. Make sure the workspace has the pi.config.json or the pi.skills.path setting (see 2.2‑C).                                                                                                       
 2. Open the Command Palette (⇧⌘P / Ctrl+Shift+P).                                                                                                                                                  
 3. Type “Agency‑Agents: Run Skill” – the command palette should surface it (provided the Agency‑Agents extension is installed).                                                                    
 4. Select it → you’ll be prompted for the skill slug (e.g., agency-healthcare-architect).                                                                                                          
 5. If the skill expects arguments, you’ll be prompted for them as well.                                                                                                                            
 6. The skill’s output (usually a markdown file or a generated prompt) will appear in a new editor tab, ready to copy‑paste or save.                                                                
                                                                                                                                                                                                    
 │ Quick shortcut: If you just want to read a skill without running it, you can also open the markdown file directly under ~/.claude/agents/ (or the skill’s folder under                           
 │ ~/pi-skills/agency-agents). VS Code will syntax‑highlight it because it’s a .md file.                                                                                                            
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 6️⃣  Running skills inside Docker / CI (no global install)                                                                                                                                          
                                                                                                                                                                                                    
 Many teams run their pipelines in containers. The pattern is:                                                                                                                                      
                                                                                                                                                                                                    
 ```dockerfile                                                                                                                                                                                      
   # Dockerfile snippet                                                                                                                                                                             
   FROM python:3.12-slim                                                                                                                                                                            
                                                                                                                                                                                                    
   # Install Pi runtime (you can also use a pre‑built image that already has it)                                                                                                                    
   RUN pip install --no-cache-dir pi-runtime   # <-- fictional package name                                                                                                                         
                                                                                                                                                                                                    
   # Bind‑mount the host’s skill repo into the container                                                                                                                                            
   WORKDIR /work                                                                                                                                                                                    
   COPY . .                                                                                                                                                                                         
                                                                                                                                                                                                    
   # Expose the skill repo as a volume (read‑only is fine)                                                                                                                                          
   VOLUME /work/pi-skills/agency-agents                                                                                                                                                             
                                                                                                                                                                                                    
   # Set the env var so Pi knows where to look                                                                                                                                                      
   ENV PI_SKILLS_PATH=/work/pi-skills/agency-agents                                                                                                                                                 
                                                                                                                                                                                                    
   # The default command can be anything, e.g. run a skill:                                                                                                                                         
   ENTRYPOINT ["pi", "agency-healthcare-architect", "--input", "design …"]                                                                                                                          
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 When the container starts, Pi sees the PI_SKILLS_PATH env var, loads the skill, and runs it – no global install on the host is required.                                                           
                                                                                                                                                                                                    
 CI Example (GitHub Actions)                                                                                                                                                                        
                                                                                                                                                                                                    
 ```yaml                                                                                                                                                                                            
   steps:                                                                                                                                                                                           
     - uses: actions/checkout@v4                                                                                                                                                                    
     - name: Set up Pi runtime                                                                                                                                                                      
       run: pip install pi-runtime   # or use a prebuilt image                                                                                                                                      
     - name: Run Healthcare Architect skill                                                                                                                                                         
       env:                                                                                                                                                                                         
         PI_SKILLS_PATH: ${{ github.workspace }}/pi-skills/agency-agents                                                                                                                            
       run: pi agency-healthcare-architect --input "draft PRD"                                                                                                                                      
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 7️⃣  Full‑Workspace Example (copy‑paste)                                                                                                                                                            
                                                                                                                                                                                                    
 Below is a minimal repo layout that you can clone and immediately start using skills from anywhere inside it.                                                                                      
                                                                                                                                                                                                    
 ```                                                                                                                                                                                                
   my-project/                                                                                                                                                                                      
   │                                                                                                                                                                                                
   ├─ pi.config.json                # ← points to the global skill repo                                                                                                                             
   │                                                                                                                                                                                                
   ├─ .pi/                          # (generated by Pi on first install)                                                                                                                            
   │   └─ config.toml               # Pi internal config (auto‑created)                                                                                                                             
   │                                                                                                                                                                                                
   ├─ scripts/                      # optional dev scripts                                                                                                                                          
   │   └─ install-skills.sh         # wrappers for `../scripts/install.sh`                                                                                                                          
   │                                                                                                                                                                                                
   ├─ src/                          # your actual code base                                                                                                                                         
   │   └─ …                                                                                                                                                                                         
   │                                                                                                                                                                                                
   └─ pi-skills/                    # <-- **git clone** the agency‑agents repo here                                                                                                                 
       └─ agency-agents/                                                                                                                                                                            
           ├─ engineering/                                                                                                                                                                          
           │   └─ engineering-frontend-developer.md                                                                                                                                                 
           ├─ product/                                                                                                                                                                              
           │   └─ product-manager.md                                                                                                                                                                
           └─ … (all other skill folders)                                                                                                                                                           
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 pi.config.json (place it at the repository root):                                                                                                                                                  
                                                                                                                                                                                                    
 ```json                                                                                                                                                                                            
   {                                                                                                                                                                                                
     "pi": {                                                                                                                                                                                        
       "skills": {                                                                                                                                                                                  
         "path": [                                                                                                                                                                                  
           "./pi-skills/agency-agents"                                                                                                                                                              
         ]                                                                                                                                                                                          
       }                                                                                                                                                                                            
     }                                                                                                                                                                                              
   }                                                                                                                                                                                                
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 Now any of the following works from any terminal inside my-project:                                                                                                                                
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # List all skills available in this workspace                                                                                                                                                    
   pi --list-skills                                                                                                                                                                                 
                                                                                                                                                                                                    
   # Run a specific skill                                                                                                                                                                           
   pi agency-healthcare-architect --input "design a price‑cap engine"                                                                                                                               
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 8️⃣  Quick‑Reference Cheat Sheet                                                                                                                                                                    
                                                                                                                                                                                                    
 ┌────────────────────────────┬─────────────────────────────────────────────────────────────────────┬───────────────────────────────────────────┐                                                   
 │ Action                     │ Command / Setting                                                   │ Where to put it                           │                                                   
 ├────────────────────────────┼─────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                   
 │ Add a global skill root    │ export PI_SKILLS_PATH="/home/me/pi-skills/agency-agents"            │ ~/.bashrc / ~/.zshrc                      │                                                   
 ├────────────────────────────┼─────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                   
 │ Add a local workspace root │ "pi.skills.path": ["/path/to/agency-agents"]                        │ pi.config.json or VS Code Settings (JSON) │                                                   
 ├────────────────────────────┼─────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                   
 │ Install a skill            │ ../scripts/install.sh --tool claude-code --division healthcare      │ From the project root                     │                                                   
 ├────────────────────────────┼─────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                   
 │ Run a skill                │ pi <slug> [options]                                                 │ Anywhere (provided the env/path is set)   │                                                   
 ├────────────────────────────┼─────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                   
 │ VS Code: Open skill UI     │ Ctrl+Shift+P → “Agency‑Agents: Run Skill”                           │ VS Code command palette                   │                                                   
 ├────────────────────────────┼─────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                   
 │ Docker: expose skill repo  │ ENV PI_SKILLS_PATH=/work/pi-skills/agency-agents                    │ Dockerfile / compose                      │                                                   
 ├────────────────────────────┼─────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────┤                                                   
 │ CI: Run a skill            │ env: PI_SKILLS_PATH=${{ github.workspace }}/pi-skills/agency-agents │ GitHub Actions step                       │                                                   
 └────────────────────────────┴─────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────┘                                                   
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 9️⃣  TL;DR – One‑liner to get started                                                                                                                                                               
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # 1️⃣ Clone the repo once                                                                                                                                                                         
   git clone https://github.com/msitarzewski/agency-agents.git ~/pi-skills/agency-agents                                                                                                            
                                                                                                                                                                                                    
   # 2️⃣ Add the path (bash)                                                                                                                                                                         
   echo 'export PI_SKILLS_PATH="$HOME/pi-skills/agency-agents:$PI_SKILLS_PATH"' >> ~/.bashrc                                                                                                        
   source ~/.bashrc                                                                                                                                                                                 
                                                                                                                                                                                                    
   # 3️⃣ Create a new project folder                                                                                                                                                                 
   mkdir -p ~/my-project && cd ~/my-project                                                                                                                                                         
   # (optional) create pi.config.json pointing at the same path                                                                                                                                     
                                                                                                                                                                                                    
   # 4️⃣ Install the skills you need                                                                                                                                                                 
   ../scripts/install.sh --tool claude-code --division healthcare                                                                                                                                   
                                                                                                                                                                                                    
   # 5️⃣ Run a skill from anywhere                                                                                                                                                                   
   pi agency-healthcare-architect --input "draft a price‑cap policy"                                                                                                                                
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 That’s it – you now have a fully‑wired skill library that can be invoked from any terminal, any IDE, any CI job, or any Docker container, without ever having to reinstall anything globally.      
                                                                                                                                                                                                    
 Feel free to ask if you need a concrete example for a particular skill (e.g., generating a PRD, converting a spec, or executing a custom script). Happy skill‑hacking! 🚀                          

 ### TL;DR – Access Agency‑Agents Skills from any VS Code workspace                                                                                                                                 
                                                                                                                                                                                                    
 Once you’ve added the PI_SKILLS_PATH (or the VS Code pi.skills.path config) and sourced it, the Pi extension does the heavy‑lifting. You only need to invoke Pi’s CLI from your VS Code Terminal   
 (or via the Command Palette). Below is the exact checklist and the few commands you’ll need.                                                                                                       
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 1️⃣ Verify Pi sees the Skill Repository                                                                                                                                                             
                                                                                                                                                                                                    
 Open VS Code Terminal → New Terminal and run:                                                                                                                                                      
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # 1. List what Pi thinks is in its skills path                                                                                                                                                   
   pi --list-skills                                                                                                                                                                                 
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 You should see something like:                                                                                                                                                                     
                                                                                                                                                                                                    
 ```                                                                                                                                                                                                
   Loaded skills:                                                                                                                                                                                   
     agency-frontend-developer  # frontend‑developer.md                                                                                                                                             
     agency-healthcare-architect # health‑related skill (if any)                                                                                                                                    
     ...                                                                                                                                                                                            
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 If you see nothing, check the env var in the terminal:                                                                                                                                             
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   echo $PI_SKILLS_PATH                                                                                                                                                                             
   # Expected: /home/you/pi-skills/agency-agents:/home/you/.pi/skills                                                                                                                               
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 If the path is wrong, fix it:                                                                                                                                                                      
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # For zshrc (global) edit:                                                                                                                                                                       
   nano ~/.zshrc                                                                                                                                                                                    
   # Append: export PI_SKILLS_PATH="/home/you/pi-skills/agency-agents:$PI_SKILLS_PATH"                                                                                                              
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 Then source ~/.zshrc or restart VS Code.                                                                                                                                                           
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 2️⃣ Invoke a Skill – Three Ways                                                                                                                                                                     
                                                                                                                                                                                                    
 ### A. Via the Pi CLI (recommended for scripts, automation, reproducible dev‑ops)                                                                                                                  
                                                                                                                                                                                                    
 Run pi from the VS Code Terminal (any folder, NOT just your project root). All commands use the same PATH you set earlier.                                                                         
                                                                                                                                                                                                    
 ┌─────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────┐ 
 │ Goal                                                    │ Command                                                                      │ Example output                                        │ 
 ├─────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤ 
 │ List all available actions                              │ pi --help                                                                    │ displays usage, common commands                       │ 
 ├─────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤ 
 │ See full skill list (including metadata)                │ pi --list-skills                                                             │ agency‑frontend‑developer,                            │ 
 │                                                         │                                                                              │ agency‑healthcare‑architect, …                        │ 
 ├─────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤ 
 │ Run a skill (with help)                                 │ pi agency-frontend-developer --help                                          │ prints the skill’s specific usage                     │ 
 ├─────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤ 
 │ Run a skill (generate a PRD for the healthcare business │ pi agency-healthcare-architect --input "draft a price‑cap engine for         │ creates a markdown design spec                        │ 
 │ case)                                                   │ emergency care"                                                              │                                                       │ 
 ├─────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤ 
 │ Run a skill (run a script to set up a project)          │ pi agency‑setup‑project --output-dir ./src                                   │ runs the script: in the agent’s frontmatter           │ 
 ├─────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤ 
 │ Run a skill (convert a markdown spec)                   │ pi agency‑convert‑markdown --format json                                     │ converts to JSON for downstream tools                 │ 
 ├─────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┤ 
 │ Get a short one‑liner                                   │ pi agency‑healthcare‑architect -i "small‑cash‑cap for ambulances"            │ quick‑fire “mini‑prompt”                              │ 
 └─────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────┘ 
                                                                                                                                                                                                    
 Quick tip: All pi commands accept the global --help flag. Example:                                                                                                                                 
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   pi agency‑healthcare‑architect --help                                                                                                                                                            
   # → prints the skill’s `script:` entry point and any options it expects                                                                                                                          
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ### B. Via VS Code Command Palette (the click‑and‑type UI)                                                                                                                                         
                                                                                                                                                                                                    
 1. Press Ctrl+Shift+P (or Cmd+Shift+P on macOS).                                                                                                                                                   
                                                                                                                                                                                                    
 2. Type (or select) a command that includes “pi” or “skill”.                                                                                                                                       
    *If the Pi extension registers a custom palette entry, you’ll see something like “Agency‑Agents: Run Skill”.*                                                                                   
                                                                                                                                                                                                    
    If you don’t see a custom entry, simply type pi and the extension will autocomplete to PI: Run Command. Choose it → it will launch a second prompt asking for the skill slug.                   
                                                                                                                                                                                                    
 3. Enter the skill slug (e.g., agency‑healthcare‑architect).                                                                                                                                       
                                                                                                                                                                                                    
 4. Provide any required arguments (the extension will prompt you if the skill needs them).                                                                                                         
                                                                                                                                                                                                    
 5. The skill’s output will appear in a new VS Code editor tab, ready to copy or save.                                                                                                              
                                                                                                                                                                                                    
 ### C. From Git Bash / Terminal (outside VS Code)                                                                                                                                                  
                                                                                                                                                                                                    
 If you have a separate terminal (putty, iTerm, etc.) you can use the same pi binary. The environment variable is global, so you don’t have to re‑connect to VS Code.                               
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # From any shell (Git Bash on Windows, iTerm on macOS, zsh, bash, etc.)                                                                                                                          
   pi --list-skills          # see what’s available                                                                                                                                                 
   pi agency‑healthcare‑architect -i "design a reimbursement API"                                                                                                                                   
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 3️⃣ Frequently‑Used “Healthcare‑Project” Skill Commands                                                                                                                                             
                                                                                                                                                                                                    
 Here are the ones most useful for your “Crisis‑Cost Orchestrator” project. Change the skill name to whatever fits your setup (the slug is always agency-<name>).                                   
                                                                                                                                                                                                    
 ┌───────────────────────────────────┬────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────┬───────────────────────────────────────────┐ 
 │ Intent                            │ Command                                                │ In Terminal                                           │ In VS Code Command Palette                │ 
 ├───────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────┤ 
 │ Generate a PRD for the healthcare │ pi agency‑healthcare‑architect -i "Generate a PRD for  │ pi agency‑healthcare‑architect -i "Generate a PRD for │ Agency‑Agents: Run Skill →                │ 
 │ use‑case                          │ a price‑cap engine for emergency care"                 │ a price‑cap engine for emergency care"                │ agency‑healthcare‑architect → answer      │ 
 ├───────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────┤ 
 │ Run a test harness (if the skill  │ pi agency‑testing‑evals                                │ pi agency‑testing‑evals                               │ same                                      │ 
 │ contains a script: test.sh)       │                                                        │                                                       │                                           │ 
 ├───────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────┤ 
 │ Inject a custom prompt into an    │ pi agency‑prompt‑optimizer -i "Add a section about     │ pi agency‑prompt‑optimizer -i "Add a section about    │ same                                      │ 
 │ existing agent                    │ HIPAA compliance"                                      │ HIPAA compliance"                                     │                                           │ 
 ├───────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────┤ 
 │ List all “engineering” division   │ `pi --list‑skills                                      │ grep engineering`                                     │ same                                      │ 
 │ skills (you may have many)        │                                                        │                                                       │                                           │ 
 ├───────────────────────────────────┼────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────┤ 
 │ Trigger a compliance check on a   │ pi agency‑healthcare‑architect --audit                 │ pi agency‑healthcare‑architect --audit                │ same                                      │ 
 │ skill                             │                                                        │                                                       │                                           │ 
 └───────────────────────────────────┴────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────┴───────────────────────────────────────────┘ 
                                                                                                                                                                                                    
 Note: The exact CLI options are defined in each agent’s script: block. The --help output tells you the exact option names.                                                                         
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 4️⃣ Quick Checklist – “Did I Get It Working?”                                                                                                                                                       
                                                                                                                                                                                                    
 ┌──────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────┐                  
 │ Step                             │ Command                                                                                    │ Expected outcome                              │                  
 ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤                  
 │ 1. Reload environment            │ source ~/.zshrc (or restart VS Code)                                                       │ $PI_SKILLS_PATH prints the agency‑agents path │                  
 ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤                  
 │ 2. List skills                   │ pi --list-skills                                                                           │ Displays “agency‑healthcare‑architect”, …     │                  
 ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤                  
 │ 3. Test a skill (help)           │ pi agency‑healthcare‑architect --help                                                      │ Shows the script name + any expected args     │                  
 ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤                  
 │ 4. Run a real command (PRD)      │ pi agency‑healthcare‑architect -i "Draft a PRD for Crisis‑Cost Orchestrator"               │ Opens a markdown file in a new tab            │                  
 ├──────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────┤                  
 │ 5. Verify the file saved/visible │ In VS Code, look for a new tab titled something like agency‑healthcare‑architect_output.md │ Should contain the generated spec             │                  
 └──────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────┘                  
                                                                                                                                                                                                    
 If any step fails:                                                                                                                                                                                 
                                                                                                                                                                                                    
 - Step 1 – double‑check echo $PI_SKILLS_PATH.                                                                                                                                                      
 - Step 2 – try pi --list‑skills --debug. It will tell you exactly why it can’t read the repo (permissions, missing file, etc.).                                                                    
 - Step 3 – ensure the skill file actually exists (ls $PI_SKILLS_PATH/*/agency-healthcare-architect.md).                                                                                            
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 5️⃣ One‑liner for instant access                                                                                                                                                                    
                                                                                                                                                                                                    
 ```bash                                                                                                                                                                                            
   # From any terminal (including VS Code Terminal)                                                                                                                                                 
   pi --list-skills && pi agency-healthcare-architect -i "Crisis‑Cost Orchestrator PRD"                                                                                                             
 ```                                                                                                                                                                                                
                                                                                                                                                                                                    
 That line will:                                                                                                                                                                                    
                                                                                                                                                                                                    
 1. List everything Pi sees in the skills path.                                                                                                                                                     
 2. Generate a PRD for your healthcare project and open it in a new VS Code editor (because the pi binary prints the markdown output to STDOUT, which VS Code captures into an editor tab).         
                                                                                                                                                                                                    
 ────────────────────────────────────────────────────────────────────────────────                                                                                                                   
                                                                                                                                                                                                    
 🎯 Bottom Line – What You Need to Remember                                                                                                                                                         
                                                                                                                                                                                                    
 ┌───────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────┐ 
 │ What                      │ Where you put it                                                                    │ How you invoke it                                                            │ 
 ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤ 
 │ Skill repository location │ ~/.zshrc (export PI_SKILLS_PATH=…) or pi.config.json or VS Code Settings            │ No manual action                                                             │ 
 │                           │ pi.skills.path                                                                      │                                                                              │ 
 ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤ 
 │ Skill discovery           │ Already part of the Pi runtime                                                      │ pi --list-skills                                                             │ 
 ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤ 
 │ Running a specific skill  │ Anywhere you have a shell with that env var                                         │ pi agency‑<slug> [options]                                                   │ 
 ├───────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤ 
 │ VS Code UI version        │ Same settings as above                                                              │ Command Palette → Agency‑Agents: Run Skill (or Ctrl+Shift+P → “PI: Run       │ 
 │                           │                                                                                     │ Command”)                                                                    │ 
 └───────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────┘ 
                                                                                                                                                                                                    
 Once those three pieces are in place, any of the 232+ agency‑agents are just one command away.                                                                                                     
                                                                                                                                                                                                    
 Feel free to ask if you need a concrete example for a different agent (e.g., agency‑backend‑architect for the API design, or agency‑security‑architect for the HIPAA hardening). Happy             
 skill‑hacking! 🚀                                                                                                                                                                                  

