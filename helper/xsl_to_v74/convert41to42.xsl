<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>


<!-- default rule -->
<xsl:template match="*" mode="conv41to42">
        <xsl:copy>
                <xsl:copy-of select="@*"/>
                     <xsl:apply-templates mode="conv41to42"/>
        </xsl:copy>  
</xsl:template>

<!-- ec2 varaibles -->
<xsl:variable name="ec2privatekey" select="/image/preferences/type/@ec2privatekeyfile"/>
<xsl:variable name="ec2cert" select="/image/preferences/type/@ec2certfile"/>
<xsl:variable name="ec2acct" select="/image/preferences/type/@ec2accountnr"/>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
        Changed attribute <tag class="attribute">schemaversion</tag>
        to <tag class="attribute">schemaversion</tag> from
        <literal>4.1</literal> to <literal>4.2</literal>. Created new
        <tag class="element">ec2config</tag> element to collect 
        <tag class="attribute">ec2*</tag> attributes. The 
        <tag class="element">ec2config</tag> element is a child of the
        <tag class="element">type</tag> element.
</para>
<xsl:template match="image" mode="conv41to42">
    <xsl:choose>
        <!-- nothing to do if already at 4.2 -->
        <xsl:when test="@schemaversion > 4.1">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.2">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv41to42"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv41to42">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv41to42"/>
    </xsl:copy>
</xsl:template>

<xsl:template match="preferences" mode="conv41to42">
        <preferences>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates mode="conv41to42"/>
        </preferences>
</xsl:template>

<xsl:template match="type" mode="conv41to42">
        <xsl:choose>
                <xsl:when test="@image='ec2'">
                        <type>
                        <xsl:for-each select="@*">
                                <xsl:choose>
                                        <xsl:when test="name()='ec2privatekeyfile'"/>
                                        <xsl:when test="name()='ec2certfile'"/>
                                        <xsl:when test="name()='ec2accountnr'"/>
                                        <xsl:otherwise>
                                            <xsl:attribute name="{local-name()}">
                                                <xsl:value-of select="."/>
                                            </xsl:attribute>
                                        </xsl:otherwise>
                                </xsl:choose>
                        </xsl:for-each>
                        <xsl:if test="$ec2privatekey or $ec2cert or $ec2acct">
                                <ec2config>
                                <xsl:if test="$ec2privatekey">
                                        <ec2privatekeyfile>
                                        <xsl:value-of select="$ec2privatekey"/>
                                        </ec2privatekeyfile>
                                </xsl:if>

                                <xsl:if test="$ec2cert">
                                        <ec2certfile>
                                        <xsl:value-of select="$ec2cert"/>
                                        </ec2certfile>
                                </xsl:if>

                                <xsl:if test="$ec2acct">
                                        <ec2accountnr>
                                        <xsl:value-of select="$ec2acct"/>
                                        </ec2accountnr>
                                </xsl:if>
                                </ec2config>
                        </xsl:if>
                        <xsl:copy-of select="current()/*"/>
                </type>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy-of select="."/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
