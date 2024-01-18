import pandas as pd

BASE_ADDRESS = 0x80000000
print(type(BASE_ADDRESS))

xls = pd.ExcelFile("csreg_gen.xlsx")
print(xls.sheet_names)
df = pd.DataFrame(pd.read_excel(xls, sheet_name="csreg"))
addr_width = '0' + str(int.bit_length(df.ndim)) + 'b'

# Lambda functions for generating code
addr = lambda x : 'addr=>(\"' + format(x, addr_width).rjust(16, '-') + '--\"),'
c_addr = lambda reg, val : '#define ' + reg.upper() + ' 0X' + format(val, '08X') + '\n'
name = lambda x : '(name=>(\"' + x.ljust(32, ' ') + '\"),'
ind = lambda x : '    ' + str(x).ljust(4,' ') + '=>'
init = lambda x : 'init=>X\"' + str(x).upper().rjust(8, '0') + '\",'
constant_index = lambda x,y : '  constant ' + x.upper().ljust(32, ' ') + ': natural := ' + str(y).rjust(2, ' ') + ';\n'
subtype_dec = lambda reg, rfld, high, low : '  subtype ' + (reg + '_' + rfld).upper().ljust(64, ' ') + 'is natural range ' + str(high).rjust(2, ' ') + ' downto ' +str(low).rjust(2, ' ') + ';\n'
const_dec = lambda reg, rfld, x : '  subtype ' + (reg + '_' + rfld).upper().ljust(64, ' ') + ' : natural              := ' + str(x).rjust(2, ' ') + ';\n'
fields = lambda x,y : 'fields=>' + x + ')' + y
desc = lambda x : ' --' + x + '\n'
hilo = lambda x,y : x + '=>' + str(y).rjust(2, ' ') +','
yn = lambda x,y : x + '=>' + y.upper() + ','
used = lambda x,y : x + '=>' + y.upper() + '),'

csregMapPack = "library ieee;\n  use ieee.std_logic_1164.all;\n  use ieee.numeric_std.all;\n\n  use work.csreg_pkg.all;\n\npackage csreg_map_pkg is\n\n"
index_constants = ''
range_constants = ''
register_fields = ''
csregMap = "-- The CSREG_MAP constant defines the registers, their addresses, intial values and access modes\n  constant CSREG_MAP : t_Reg_Map_Array := (\n"

dotHfile = '// Control and Status register addresses\n'

# Generate CSREG_MAP
for index, row in df.iterrows():
  reg_name = row["Name"]
  regAddr = (index * 4) + BASE_ADDRESS
  line_end = '' if index == df.index[-1] else ','
  # print(ind(index), name(reg_name), addr(index), init(row["Init"]), yn('wrInt',(row["wrInt"])), yn('rdInt',(row["rdInt"])), fields(row["Fields"], line_end), desc(row["Description"]))
  csregMap = csregMap + ind(index) + name(reg_name) + addr(index) + init(row["Init"]) + yn('wrInt',(row["wrInt"])) + yn('rdInt',(row["rdInt"])) + fields(row["Fields"], line_end) + desc(row["Description"])
  index_constants = index_constants + constant_index(reg_name, index)
  dotHfile = dotHfile + c_addr(reg_name, regAddr)
csregMap = csregMap + '  );\n\n'

print(dotHfile)

# List of register fields from Excel spreadsheet
df_fields = pd.DataFrame(pd.read_excel(xls, sheet_name="fields"))
field_list = df_fields['FIELD'].tolist()

# Generate the register field constants
for fld in field_list:
  df = pd.DataFrame(pd.read_excel(xls, sheet_name=fld))
  # print("  constant", fld, ': t_Field_Map_Array := (' )
  register_fields = register_fields + "  constant " + fld + ' : t_Field_Map_Array := (\n'
  for index, row in df.iterrows():
    hi = row['hi']
    lo = row['lo']
    fieldName = row['Name']
    # print(ind(index), name(fieldName), hilo('hi', hi),hilo('lo', lo), yn('ro', row['ro']), yn('static', row['static']), yn('used', row['used']), desc(row['Description']))
    register_fields = register_fields + ind(index) + name(fieldName) + hilo('hi', hi) + hilo('lo', lo) + yn('ro', row['ro']) + yn('static', row['static']) + used('used', row['used']) + desc(row['Description'])
    if not(fieldName.isspace()):
      if hi == lo:
        range_constants = const_dec(fld, fieldName, hi) + range_constants
      else:
        range_constants = subtype_dec(fld, fieldName, hi, lo) + range_constants
        
  register_fields = register_fields + '    others => UNUSED FIELD\n  );\n\n'

# print(register_fields)
# print(csregMap)
index_constants = "-- Index constants to simplify accessing the registers\n" + index_constants
# print(index_constants)
  
range_constants = "\n-- Range constants are declared to simplify accessing fields in a register\n" + range_constants
# print(range_constants)

csregMapPack = csregMapPack + register_fields + csregMap + index_constants + range_constants + '\n\nend package csreg_map_pkg;'

with open('./csreg_map_pkg.vhd', 'w') as f:
  f.write(csregMapPack)

with open('./csreg.h', 'w') as f:
  f.write(dotHfile)



# Extraneous print statements for debugging
# print(df.keys())
# print(df.ndim)
# print(df.loc[0,"Name"])
# print(format(6, '06b'))
# print(int.bit_length(df.ndim))
# print(addr_width)
# print(format(1, addr_width))
# print(df_fields)
# print(df_fields.loc[:, 'FIELD'])
# print(field_list)