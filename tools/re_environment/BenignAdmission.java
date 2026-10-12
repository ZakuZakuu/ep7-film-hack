// Original headless admission script. Run ONLY on the synthetic demo ELF.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.nio.file.Files;
import java.nio.file.Path;

public class BenignAdmission extends GhidraScript {
    @Override public void run() throws Exception {
        if (!currentProgram.getName().equals("demo")) {
            throw new IllegalArgumentException("Synthetic demo only");
        }
        int count = 0;
        boolean found = false;
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        while (it.hasNext()) {
            Function f = it.next();
            count++;
            if (f.getName().equals("film_style_demo")) {
                found = true;
                if (currentProgram.getListing().getInstructionAt(f.getEntryPoint()) == null)
                    throw new IllegalStateException("Missing synthetic instruction");
            }
        }
        if (!found) throw new IllegalStateException("Missing synthetic function");
        Files.writeString(Path.of(getScriptArgs()[0]),
            "{\"headless\":\"pass\",\"synthetic_function_found\":true,\"function_count\":" + count + "}\n");
    }
}
